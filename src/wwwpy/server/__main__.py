from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Optional, Sequence, NamedTuple

from wwwpy.server.convention import start_default
from wwwpy.server.tcp_port import find_port

logger = logging.getLogger(__name__)


class Arguments(NamedTuple):
    directory: Path
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
        directory=Path(parsed_args.directory).absolute(),
        port=parsed_args.port,
        dev=bool(parsed_args.dev)
    )


def _open_browser(args, settings):
    import webbrowser
    if settings.open_url_code:
        loc = {'url': f'http://localhost:{args.port}', args: args}
        exec(settings.open_url_code, loc, loc)
    else:
        webbrowser.open(f'http://localhost:{args.port}')


def main():
    import wwwpy
    print(f'Starting wwwpy v{wwwpy.__version__}')
    args = parse_arguments()
    if args.port == 0:
        args = args._replace(port=find_port())
    project = start_default(args.directory, args.port, dev_mode=args.dev)
    _open_browser(args, project.settings)
    try:
        from wwwpy.webserver import wait_forever
        wait_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
