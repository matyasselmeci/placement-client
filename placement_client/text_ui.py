"""
Interactively get a token using the device flow.
"""

import datetime
import os

# import time
import typing as t

from placement_client import common  # , device
from placement_client.device import DEFAULT_CLIENT_ID, DeviceClient, DeviceClientError


def request_token_and_return(
    placement_server: str, client_id: t.Optional[str] = None
) -> t.Optional[bytes]:
    """
    Requests a token interactively and returns it as bytes.

    Arguments:
        placement_server:
            The placement webapp server URL or hostname for the device flow.
        client_id:
            The name to use as the client identifier for the DeviceClient.
            If not provided, defaults to the DEVICE_CLIENT_ID environment variable,
            or DEFAULT_CLIENT_ID if that is not set.

    Returns:
        The token as bytes or None.
    """
    if client_id is None:
        client_id = os.environ.get("DEVICE_CLIENT_ID") or DEFAULT_CLIENT_ID

    dc = DeviceClient(
        placement_server=placement_server,
        client_id=client_id,
    )

    try:
        dc.make_request()
    except DeviceClientError as err:
        print(f"Request to {dc.placement_server} failed: {err}")
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
        access_token_b = dc.wait_for_token()
    except DeviceClientError as err:
        print(f"Request to {dc.placement_server} failed: {err}")
        return None

    print("Request successful!")
    return access_token_b


def request_token(
    placement_server: str,
    client_id: t.Optional[str] = None,
    token_filename: str = common.TOKEN_FILENAME,
) -> bool:
    """
    Request a token and install it into the user tokens directory.

    Args:
        placement_server:
            The placement server URL or hostname for the device flow.
        client_id:
            The name to use as the client identifier for the DeviceClient.
            If not provided, defaults to the DEVICE_CLIENT_ID environment variable,
            or DEFAULT_CLIENT_ID if that is not set.
        token_filename:
            The basename of the token file to write.  May not contain directory
            components.

    Returns:
        bool: True on success, False on failure.
    """
    token_contents = request_token_and_return(placement_server, client_id)
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
