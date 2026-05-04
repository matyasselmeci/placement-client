import base64
import datetime
import enum
import json
import logging
import os
import pathlib
import time
import typing as t

import classad2

_log = logging.getLogger(__name__)


class TokenState(enum.Enum):
    MISSING = "MISSING"
    UNREADABLE = "UNREADABLE"
    EXPIRED = "EXPIRED"
    OK = "OK"


T_Constraint = t.Union["classad2.ExprTree", str]
T_PathOrStr = t.Union[os.PathLike, str]


TOKEN_FILENAME = "Placement.token"
WEBAPP_SERVER = os.environ.get("PLACEMENT_WEBAPP_LINK") or "http://localhost:5000"


#
#
# Utils for installing the token once obtained
#
#


def get_condor_tokens_dir(*, create: bool = False) -> pathlib.Path:
    """
    Get the path to the condor tokens directory.

    Arguments:
        create:
            If set, will create the directory if necessary and fix its
            permissions.

    Returns:
        A pathlib.Path to the tokens directory.
    """
    try:
        # The SEC_TOKEN_DIRECTORY parameter is the location where condor looks
        # for tokens; if it is not set or empty, then condor uses ~/.condor/tokens.d.
        import htcondor2  # type: ignore

        # ^^ ignore this: we catch the ImportError and fall back to the default path

        sec_token_directory = htcondor2.param["SEC_TOKEN_DIRECTORY"]
        if sec_token_directory:
            condor_tokens_dir = pathlib.Path(sec_token_directory)
        else:
            raise ValueError()  # catch this
    except (KeyError, ValueError, ImportError):
        condor_tokens_dir = pathlib.Path.home() / ".condor/tokens.d"

    if create:
        condor_tokens_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        condor_tokens_dir.chmod(
            0o700
        )  # mkdir doesn't set the mode if it already exists

    return condor_tokens_dir


def write_token(token_filename: str, token_contents: bytes) -> pathlib.Path:
    """
    Write the given bytes to a token file in the condor tokens dir.

    Arguments:
        token_filename:
            The name of the file (without directory) to create
            under the tokens directory.  (Should end in '.token')

        token_contents: The bytes to write into the token file.

    Returns:
        The path to where the file was written.
    """
    if "/" in token_filename or "\\" in token_filename or ":" in token_filename:
        raise ValueError(f"token_filename cannot have a directory: {token_filename}")
    condor_tokens_dir = get_condor_tokens_dir(create=True)
    token_dest = condor_tokens_dir / token_filename
    with open(token_dest, mode="wb") as fh:
        token_dest.chmod(0o600)
        fh.write(token_contents)
    return token_dest


def token_stat(token_filename: str) -> t.Optional[os.stat_result]:
    """
    Calls stat() on the token file and returns the results.  If there is
    an error (e.g., the file does not exist), returns None.
    """
    if "/" in token_filename or "\\" in token_filename or ":" in token_filename:
        raise ValueError(f"token_filename cannot have a directory: {token_filename}")
    condor_tokens_dir = get_condor_tokens_dir()
    token_dest = condor_tokens_dir / token_filename
    try:
        return token_dest.stat()
    except OSError:
        return None


def get_token_state(
    token_filename: str,
) -> TokenState:
    """
    Return whether the token is expired, missing, unreadable, or OK
    """
    if "/" in token_filename or "\\" in token_filename or ":" in token_filename:
        raise ValueError(f"token_filename cannot have a directory: {token_filename}")
    token_path = get_condor_tokens_dir() / token_filename
    try:
        contents = token_path.read_bytes()
    except FileNotFoundError as err:
        _log.debug("%s not found", token_path)
        return TokenState.MISSING
    except OSError as err:
        _log.debug("OSError(%s) reading token %s", err, token_path)
        return TokenState.UNREADABLE
    try:
        body = contents.split(b'.')[1]
        body_json = json.loads(base64.urlsafe_b64decode(body + b'=='))
        expiration = float(body_json["exp"])
    except (IndexError, ValueError) as err:
        _log.debug("Error %s decoding token %s", err, token_path, exc_info=True)
        return TokenState.UNREADABLE
    if expiration < time.time():
        return TokenState.EXPIRED
    return TokenState.OK


def describe_token(
    token_filename: str = TOKEN_FILENAME,
    collector_host: t.Optional[str] = None,
    schedd_host: t.Optional[str] = None,
) -> None:
    try:
        import htcondor2  # type: ignore
    except ImportError:
        print("htcondor2 module not found; cannot describe token.")
        return

    if collector_host:
        collector = htcondor2.Collector(collector_host)
    else:
        collector = htcondor2.Collector()
    schedd_host = schedd_host or htcondor2.param["SCHEDD_HOST"]
    schedd_ad = collector.locate(htcondor2.DaemonType.Schedd, schedd_host)
    schedd = htcondor2.Schedd(schedd_ad)

    project = None
    user = None
    # have_read = False
    # have_write = False
    ad = {}
    text = []

    state = get_token_state(token_filename)

    if state == TokenState.MISSING:
        print("The token file is missing")
        return
    elif state == TokenState.UNREADABLE:
        print("The token file cannot be read or is not a recognizable token")
        return
    elif state == TokenState.EXPIRED:
        print("The token is expired.")
        return
    elif state == TokenState.OK:
        pass

    try:
        ad = htcondor2.ping(schedd_ad, "READ")
        # have_read = True
        # ^^ maybe also check ad['AuthorizationSucceeded'] ?
        text.append(
            "You can list jobs and view the details of jobs with your current token."
        )
    except htcondor2.HTCondorException as err:
        if "Failed to start command" in str(err):
            # have_read = False
            text.append(
                "You CANNOT list jobs or view the details of jobs with your current token."
            )
        else:
            raise
    try:
        ad = htcondor2.ping(schedd_ad, "WRITE")
        # have_write = True
        # ^^ maybe also check ad['AuthorizationSucceeded'] ?
        user_ad = (schedd.queryUserAds(constraint=f'User=="{user}"') or [{}])[0]  # fmt: skip
        # ^^ TODO We can't do this query if we don't have READ.
        if user_ad.get("Enabled", True):
            text.append(
                "You can place, remove, edit, hold, release, and otherwise manipulate jobs with your current token."
            )
        else:
            text.append(
                "You can remove, edit, hold, release, and otherwise manipulate existing jobs with your current token."
            )
            text.append(
                "However, you CANNOT place new jobs, and your existing jobs will not start."
            )
    except htcondor2.HTCondorException as err:
        if "Failed to start command" in str(err):
            # have_read = False
            text.append(
                "You CANNOT place, remove, edit, hold, release, or otherwise manipulate jobs with your current token."
            )
        else:
            raise
    project = ad.get("AuthTokenProject")
    user = ad.get("MyRemoteUserName")
    if user:
        text.append(f"Your AP User ID is '{user}'.")
    else:
        text.append("ERROR: Your AP User ID is unknown.")  # XXX how can this happen?
    if project:
        text.append(f"Your currently selected project is '{project}'.")
    else:
        text.append("WARNING: Your currently selected project is unknown.")

    print("\n".join(text))
