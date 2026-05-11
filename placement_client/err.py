"""
err.py
------

Exception hierarchy for the placement_client package.
"""


class DeviceClientError(Exception):
    """Errors while trying to the device flow."""


class DeviceClientInitialRequestError(DeviceClientError):
    """Some failure to make the initial request to the remote server."""


class DeviceClientUnexpectedOutput(DeviceClientError):
    """Server responded with something unexpected."""


class DeviceClientTimedOut(DeviceClientError):
    """The device flow session expired."""


class DeviceClientRequestNotInProgress(DeviceClientError):
    """No device flow session is in progress."""


class DeviceClientAccessDenied(DeviceClientError):
    """The user denied the token request."""
