"""
Command-line interface for the placement client.
"""

import argparse
import sys

from placement import device, cli


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="placement",
        description="placement client command-line interface",
    )
    subparsers = parser.add_subparsers(dest="subcommand", metavar="SUBCOMMAND")
    subparsers.required = True
    _add_request_token_subcommand(subparsers)
    args = parser.parse_args()
    sys.exit(args.func(args))


def _add_request_token_subcommand(subparsers) -> None:
    sub = subparsers.add_parser(
        "request-token",
        aliases=["req"],
        help="request a placement token via the device flow",
        description=(
            "Authenticate with a Placement server using the OAuth2 device flow "
            "and install the resulting token."
        ),
    )
    sub.add_argument(
        "placement_server",
        metavar="PLACEMENT_SERVER",
        help="hostname or URL of the Placement server",
    )
    sub.add_argument(
        "--client-name",
        default=None,
        metavar="NAME",
        help='client identifier sent to the server (default: "Python Script")',
    )
    sub.set_defaults(func=_handle_request_token)


def _handle_request_token(args: argparse.Namespace) -> int:
    kwargs: dict = {"placement_server": args.placement_server}
    if args.client_name is not None:
        kwargs["client_name"] = args.client_name

    success = cli.request_token(**kwargs)
    return 0 if success else 1


if __name__ == "__main__":
    main()
