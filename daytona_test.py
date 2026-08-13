"""Daytona SDK connectivity test.

Creates a sandbox, runs a trivial command, prints the result, then deletes
the sandbox.  The API key is read from the DAYTONA_API_KEY environment
variable — never hardcoded.
"""

import os
import sys

from daytona import Daytona, DaytonaConfig


def main() -> None:
    api_key = os.environ.get("DAYTONA_API_KEY")
    if not api_key:
        print("ERROR: DAYTONA_API_KEY environment variable is not set.")
        sys.exit(1)

    config = DaytonaConfig(api_key=api_key)
    daytona = Daytona(config)

    sandbox = None
    try:
        print("Creating sandbox...")
        sandbox = daytona.create()
        print(f"Sandbox created: id={sandbox.id}")

        print("Running test command...")
        response = sandbox.process.code_run(
            'print("Daytona connection successful")'
        )
        print(f"Exit code : {response.exit_code}")
        print(f"Output    : {response.result}")

    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")
        sys.exit(1)

    finally:
        if sandbox is not None:
            print("Deleting sandbox...")
            try:
                daytona.delete(sandbox)
                print("Sandbox deleted.")
            except Exception as cleanup_exc:
                print(f"Cleanup warning: {cleanup_exc}")


if __name__ == "__main__":
    main()
