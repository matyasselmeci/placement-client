"""
Command-line interface for the placement client.
"""

import argparse
import sys

from placement import device, cli


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="placement-request",
        description=(
            "Authenticate with a Placement server using the OAuth2 device flow "
            "and install the resulting token."
        ),
    )
    parser.add_argument(
        "placement_server",
        metavar="PLACEMENT_SERVER",
        help="hostname or URL of the Placement server",
    )
    parser.add_argument(
        "--client-id",
        default=None,
        metavar="ID",
        help=f'client identifier sent to the server (default: "{device.DEFAULT_CLIENT_ID}")',
    )
    args = parser.parse_args()

    kwargs: dict = {"placement_server": args.placement_server}
    if args.client_id is not None:
        kwargs["client_id"] = args.client_id

    success = cli.request_token(**kwargs)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
