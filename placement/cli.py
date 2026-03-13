"""
Interactively get a token using the device flow.
"""

import datetime

# import time
import typing as t

from placement import common  # , device
from placement.device import DeviceClient, DeviceClientError


def init_default_deviceclient() -> DeviceClient:
    """
    Create a DeviceClient with default settings.
    """
    # TODO This should take config from elsewhere (Condor config?)
    return DeviceClient(
        webapp_server=common.WEBAPP_SERVER,
        client_id=common.DEVICE_CLIENT_ID,
    )


def request_token_and_return(
    webapp_server: str, client_name: str = "Python Script"
) -> t.Optional[bytes]:
    """
    Requests a token interactively and returns it as bytes.

    Arguments:
        webapp_server:
            The URL of the web application server for the device flow.
        client_name:
            The name to use as the client_id for the DeviceClient.
            Defaults to "Python Script".

    Returns:
        The token as bytes or None.
    """
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
