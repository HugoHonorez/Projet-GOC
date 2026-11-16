import argparse

from .config import Settings
from .server.app import serve


def parse_args():
    parser = argparse.ArgumentParser(prog="python -m visualizer")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--instances", help="directory containing Instance_*.qasm")
    parser.add_argument("--solutions", action="append", help="directory scanned for solution files (repeatable)")
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    settings = Settings.create(args.instances, args.solutions)
    serve(settings, args.host, args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
