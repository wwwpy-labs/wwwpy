from __future__ import annotations

import os
import argparse
from pathlib import Path
from typing import NamedTuple, Optional, Sequence

class Arguments(NamedTuple):
    directory: str
    port: int
    dev: bool


def parse_arguments(args: Optional[Sequence[str]] = None) -> Arguments:
    parser = argparse.ArgumentParser(prog='wwwpy')
    parser.add_argument('dev', nargs='?', const=True, default=False,
                        help="Run in development mode")
    parser.add_argument('--directory', '-d', default=os.getcwd(),
                        help='set the root path for the project (default: current directory)')
    parser.add_argument('--port', type=int, default=8000,
                        help='bind to this port (default: 8000)')

    parsed_args = parser.parse_args(args)
    return Arguments(
        directory=parsed_args.directory,
        port=parsed_args.port,
        dev=bool(parsed_args.dev)
    )


def run_server(args: Arguments):
    from wwwpy.server import configure
    from wwwpy.webserver import wait_forever
    import webbrowser

    working_dir = Path(args.directory).absolute()
    configure.start_default(args.port, working_dir, dev_mode=args.dev)
    webbrowser.open(f'http://localhost:{args.port}')
    wait_forever()


def main():
    args = parse_arguments()
    run_server(args)


if __name__ == '__main__':
    main()
