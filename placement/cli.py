"""
Interactively get a token using the device flow.
"""

import datetime
import os

# import time
import typing as t

from placement import common  # , device
from placement.device import DeviceClient, DeviceClientError


def request_token_and_return(
    webapp_server: str, client_name: t.Optional[str] = None
) -> t.Optional[bytes]:
    """
    Requests a token interactively and returns it as bytes.

    Arguments:
        webapp_server:
            The URL of the web application server for the device flow.
        client_name:
            The name to use as the client_id for the DeviceClient.
            If not provided, defaults to the DEVICE_CLIENT_NAME environment variable,
            or "Python Script" if that is not set.

    Returns:
        The token as bytes or None.
    """
    if client_name is None:
        client_name = os.environ.get("DEVICE_CLIENT_NAME") or "Python Script"

    dc = DeviceClient(
        webapp_server=webapp_server,
        client_id=client_name,
    )

    try:
        dc.make_request()
    except DeviceClientError as err:
        print(f"Request to {dc.webapp_server} failed: {err}")
        return None

    expires_at_dt = datetime.datetime.fromtimestamp(dc.expires_at).astimezone()
    if expires_at_dt.tzname() == "UTC":
        expformat = "%Y-%m-%d %H:%M:%S UTC"
    else:
        expformat = "%Y-%m-%d %H:%M:%S"

    print(
        f"Token requested; please go to\n\n\t{dc.verification_uri_complete}\n\n"
        f'and use the code "{dc.user_code}".\n'
        f"The code will expire at {expires_at_dt.strftime(expformat)}."
    )
    try:
        access_token_b = dc.poll_for_token_loop()
    except DeviceClientError as err:
        print(f"Request to {dc.webapp_server} failed: {err}")
        return None

    print("Request successful!")
    return access_token_b


def request_token(
    webapp_server: str,
    client_name: str = "Python Script",
    token_filename: str = common.TOKEN_FILENAME,
) -> bool:
    """
    Request a token and install it into the user tokens directory.

    Args:
        webapp_server:
            The URL of the web application server for the device flow.
        client_name:
            The name to use as the client_id for the DeviceClient.
            Defaults to "Python Script".
        token_filename:
            The basename of the token file to write.  May not contain directory
            components.

    Returns:
        bool: True on success, False on failure.
    """
    token_contents = request_token_and_return(webapp_server, client_name)
    if not token_contents:
        return False
    try:
        token_path = common.write_token(
            token_filename=token_filename, token_contents=token_contents
        )
        print(f"Token has been installed at {token_path}")
        return True
    except OSError as err:
        print(f"Token failed to install: {err}")
        return False
