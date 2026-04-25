"""
device.py
-----------

This module provides the DeviceClient class for handling OAuth2 Device Flow authentication.
It allows a client to obtain an access token by guiding the user through the device authorization process.

Features:
- Initiates device authorization requests
- Polls for token completion
- Handles device code expiration, polling intervals, and error conditions

Usage:
    client = DeviceClient(placement_server, client_name)
    client.make_request()
    # Display client.user_code and client.verification_uri to the user
    token = client.wait_for_token()
    # Use the token as needed
"""

import json
import logging
import time
import typing as t
import urllib.error
import urllib.parse
import urllib.request

_log = logging.getLogger(__name__)


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


class DeviceClient:
    """
    Client for obtaining tokens via OAuth2 Device Flow.

    This class handles the device flow authorization process, including:
    - Making the initial device authorization request
    - Polling for token completion
    - Managing device code expiration and polling intervals
    """

    GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
    REQUEST_ENDPOINT = "/auth/device_authorization"

    def __init__(self, placement_server: str, client_name: str):
        """
        Initialize the DeviceClient.

        Args:
            placement_server: The placement server URL as a hostname, host:port,
                or IP address (with optional scheme). If no scheme is specified,
                http:// is used for localhost, https:// for other hosts.
            client_name: The client identifier. Must start with a letter or number
                and be less than 80 characters.

        Raises:
            ValueError: If placement_server is invalid, if client_name doesn't
                start with a letter or number, or if client_name is 80
                characters or longer.
        """
        # Validate and transform placement_server
        placement_server = self._validate_and_transform_server(placement_server)

        # Validate client_name
        if not client_name:
            raise ValueError("client_name cannot be empty")
        if not client_name[0].isalnum():
            raise ValueError("client_name must start with a letter or number")
        if len(client_name) >= 80:
            raise ValueError("client_name must be less than 80 characters")

        self.placement_server = placement_server
        self.request_url = f"{placement_server}{self.REQUEST_ENDPOINT}"
        self.client_name = client_name
        self._reset_attrs()

    @staticmethod
    def _validate_and_transform_server(server: str) -> str:
        """
        Validate and transform the placement server URL.

        If no scheme is provided, http:// is added for localhost, https:// otherwise.

        Args:
            server: The server URL/hostname/IP address.

        Returns:
            The validated and transformed server URL.

        Raises:
            ValueError: If the server format is invalid.
        """
        if not server:
            raise ValueError("placement_server cannot be empty")

        # Check if a scheme is present
        # Note: If a port is specified (e.g. 'localhost:5000'), urlparse thinks
        # "localhost" is the scheme.
        if "//" in server:
            parsed = urllib.parse.urlparse(server)
        else:
            parsed = urllib.parse.urlparse(f"//{server}")
        if parsed.scheme:
            # Has a scheme; validate it
            if parsed.scheme not in ("http", "https"):
                raise ValueError(
                    f"Invalid scheme '{parsed.scheme}'; must be 'http' or 'https'"
                )
            # Verify netloc is present
            if not parsed.netloc:
                raise ValueError("Invalid URL: missing hostname")
            return server
        else:
            netloc = parsed.netloc

            if not netloc:
                raise ValueError("Invalid placement_server format")

            # Extract hostname (remove port if present)
            hostname = netloc.split(":")[0]

            # Use http for localhost, https for others
            if hostname == "localhost":
                return f"http://{netloc}"
            else:
                return f"https://{netloc}"

    def _reset_attrs(self):
        self.device_code = ""
        self.expires_at = 0.0
        self.interval = 0
        self.user_code = ""
        self.verification_uri = ""
        self.verification_uri_complete = ""
        self.request_in_progress = False
        self.access_token = b""

    def _post_form_json(
        self,
        data: t.Mapping[str, str],
        *,
        connection_error_cls: t.Type[DeviceClientError],
        connection_error_message: str,
    ) -> t.Tuple[int, t.Any]:
        """Submit form data and parse a JSON response.

        Sends a ``POST`` request to ``self.request_url`` with URL-encoded form
        data. HTTP error responses are treated as valid responses so callers can
        inspect the returned status code and payload.

        Args:
            data: Form fields to encode in the request body.
            connection_error_cls: Exception type to raise for transport-level
                failures.
            connection_error_message: Prefix text for connection failure error
                messages.

        Returns:
            A ``(status_code, response_json)`` tuple where ``status_code`` is the
            HTTP status code and ``response_json`` is the decoded JSON payload.

        Raises:
            connection_error_cls: If the request cannot be sent or completed due
                to a connection-level error.
            DeviceClientUnexpectedOutput: If the response body is not valid UTF-8
                JSON.
        """
        encoded_data = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(
            url=self.request_url,
            data=encoded_data,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(request) as response:
                status_code = response.getcode()
                body = response.read()
        except urllib.error.HTTPError as err:
            status_code = err.code
            body = err.read()
        except OSError as err:
            raise connection_error_cls(
                "%s: %s" % (connection_error_message, err)
            ) from err

        try:
            response_json = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            raise DeviceClientUnexpectedOutput("Invalid JSON: %s" % err)
        return status_code, response_json

    def make_request(self) -> "DeviceClient":
        """
        Starts the session for the device flow by making the initial request
        to the placement server for the token.

        Returns self for convenience.

        Raises:
            DeviceClientInitialRequestError:
                If we couldn't connect to the server or got an immediate
                error response.
            DeviceClientUnexpectedOutput:
                If the message from the server is malformed somehow.
        """
        self._reset_attrs()
        status_code, rj = self._post_form_json(
            data={"client_id": self.client_name},
            connection_error_cls=DeviceClientInitialRequestError,
            connection_error_message="Initial request failed to connect to server",
        )
        if status_code >= 400:
            msg = "Initial request resulted in HTTP %d" % status_code
            if isinstance(rj, dict):
                error = rj.get("error")
                if error is not None:
                    msg += "; message from server: %s" % error
            raise DeviceClientError(msg)
        try:
            self.device_code = rj["device_code"]
            expires_in = rj["expires_in"]
            self.expires_at = time.time() + float(expires_in)
            self.interval = int(rj.get("interval", 5))
            self.user_code = rj["user_code"]
            self.verification_uri = rj["verification_uri"]
            self.verification_uri_complete = rj.get(
                "verification_uri_complete", self.verification_uri
            )
        except (TypeError, KeyError) as err:
            raise DeviceClientUnexpectedOutput("Server response missing %s" % err)
        except ValueError as err:
            raise DeviceClientUnexpectedOutput(
                "Server responded with unexpected output %s" % err
            ) from err
        self.request_in_progress = True
        return self

    def poll_for_token(self) -> t.Optional[bytes]:
        """
        Poll the placement server performing the device flow for the token.
        Returns the token; also sets self.access_token to the token.

        Returns:
            The placement token encoded as bytes if successful, None if
            authorization is still pending.

        Raises:
            DeviceClientRequestNotInProgress: If no device flow session is in progress.
            DeviceClientUnexpectedOutput: If the server response is invalid or unexpected.
            DeviceClientAccessDenied: If the user denied the token request.
            DeviceClientTimedOut: If the device code has expired.
            DeviceClientError: If connection to server is lost.
        """
        if not self.request_in_progress:
            raise DeviceClientRequestNotInProgress()
        status_code, response_json = self._post_form_json(
            data={
                "client_id": self.client_name,
                "grant_type": self.GRANT_TYPE,
                "device_code": self.device_code,
            },
            connection_error_cls=DeviceClientError,
            connection_error_message="Lost connection to server",
        )

        if status_code == 400:
            try:
                error: str = response_json["error"]
            except (TypeError, KeyError):
                raise DeviceClientUnexpectedOutput("Unknown failure from server")
            if error == "authorization_pending":
                return None
            if error == "slow_down":
                self.interval += 5
                _log.debug("Received slow_down; interval set to %d", self.interval)
                return None
            if error == "access_denied":
                raise DeviceClientAccessDenied()
            if error == "expired_token":
                raise DeviceClientTimedOut("Server responds device code expired")

            raise DeviceClientUnexpectedOutput(
                "Server responds with unexpected failure %s" % error
            )

        elif status_code == 200:
            try:
                access_token = response_json["access_token"]
                token_type = response_json["token_type"]
                # expires_in = response_json.get("expires_in", None)
            except (TypeError, KeyError) as err:
                raise DeviceClientUnexpectedOutput("Response missing %s" % err)
            if token_type.lower() != "placement":
                raise DeviceClientUnexpectedOutput(
                    "Unexpected token type %s" % token_type
                )
            try:
                access_token_b = access_token.encode()
            except (TypeError, AttributeError, UnicodeEncodeError) as err:
                raise DeviceClientUnexpectedOutput(
                    "Failed to encode access token: %r" % err
                )
            self.access_token = access_token_b
            return access_token_b

    def wait_for_token(self) -> bytes:
        """
        Polls the placement server until a token is returned or the device code expires.

        Returns:
            The placement token encoded as bytes.

        Raises:
            DeviceClientRequestNotInProgress: If no device flow session is in progress.
            DeviceClientTimedOut: If the device code has expired before authorization.
            DeviceClientError: If a connection error occurs during polling.
            DeviceClientAccessDenied: If the user denied the token request.
            DeviceClientUnexpectedOutput: If the server returns malformed JSON.
        """
        if not self.request_in_progress:
            raise DeviceClientRequestNotInProgress()

        while time.time() < self.expires_at:
            access_token_b = self.poll_for_token()
            if access_token_b is None:
                time.sleep(self.interval)
            else:
                return access_token_b

        raise DeviceClientTimedOut("Device code expired")
