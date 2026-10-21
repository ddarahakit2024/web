"""Serve the built Vue app, falling back to index.html for client routes."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


class SpaHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        relative_path = unquote(urlsplit(path).path).lstrip("/")
        candidate = (Path(self.directory) / relative_path).resolve()
        root = Path(self.directory).resolve()
        if not candidate.is_relative_to(root):
            return str(root / "__not_found__")
        if candidate.is_file():
            return str(candidate)
        if not Path(relative_path).suffix:
            return str(root / "index.html")
        return str(candidate)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--bind", default="0.0.0.0")
    args = parser.parse_args()

    handler = partial(SpaHandler, directory=args.directory)
    server = ThreadingHTTPServer((args.bind, args.port), handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
