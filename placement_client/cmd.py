"""
Command-line interface for the placement client.
"""

import argparse
import sys
import traceback

from placement_client import common, text_ui


def print_failure_message():
    print("Token NOT created.", file=sys.stderr)
    print("You will have to re-run the program to get a token.", file=sys.stderr)


def get_args(argv) -> argparse.Namespace:
    default_token_name = common.TOKEN_FILENAME.split(".")[0]  # chop off the .token
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
        "-n",
        "--token-name",
        default=default_token_name,
        help="Name of the token to create (default: %(default)s)",
    )
    args = parser.parse_args(argv[1:])
    if any(sep in args.token_name for sep in ("/", "\\", ":")):
        parser.error("Token name may not contain path separators ('/', '\\', ':').")
    return args


def main(argv=()) -> int:
    try:
        args = get_args(argv or sys.argv)
        token_filename = args.token_name
        if "." not in token_filename:
            token_filename += ".token"
        success = text_ui.request_token(
            placement_server=args.placement_server, token_filename=token_filename
        )
        if success:
            return 0
        else:
            print_failure_message()
            return 1
    except KeyboardInterrupt:
        print("\nRequest interrupted.")
        print_failure_message()
        return 130
    except Exception as err:
        # Print the exception traceback but then also let the user know that
        # they have to re-run the program to get a token.
        traceback.print_exc()
        print(f"\nError: {err}", file=sys.stderr)
        print_failure_message()
        return 1


if __name__ == "__main__":
    sys.exit(main())
