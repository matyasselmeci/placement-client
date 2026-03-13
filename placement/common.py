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
        import htcondor2

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


TOKEN_FILENAME = "Placement.token"
WEBAPP_SERVER = os.environ.get("PLACEMENT_WEBAPP_LINK") or "http://localhost:5000"
