#!/usr/bin/env python3
"""Count game files that cannot be resolved using a hash list."""

import argparse
import os
from pathlib import Path
import sys

from prune import HASHED_NAME, canonical_hash, load_type_ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hashlist", type=Path, help="Input hash list")
    parser.add_argument("game_folder", type=Path, help="Game data folder")
    parser.add_argument("file_types", type=Path, help="File associations (DDFMap.txt)")
    args = parser.parse_args()
    if not args.game_folder.is_dir():
        parser.error(f"Not a directory: {args.game_folder}")

    type_ids = load_type_ids(args.file_types)
    names, keys = set(), set()
    for number, line in enumerate(args.hashlist.read_text(encoding="utf-8-sig").splitlines(), 1):
        fields = line.strip().split(maxsplit=1)
        if len(fields) != 2:
            raise ValueError(f"Invalid hash-list entry on line {number}: expected two names")
        hashed, _ = fields
        names.add(hashed.casefold())
        key = canonical_hash(hashed, type_ids)
        if key is not None:
            keys.add(key)

    def fail(error):
        raise error

    total = hashed_count = unresolved = 0
    for _, _, files in os.walk(args.game_folder, onerror=fail):
        for name in files:
            total += 1
            if not HASHED_NAME.fullmatch(name.casefold()):
                continue
            hashed_count += 1
            key = canonical_hash(name, type_ids)
            if name.casefold() not in names and (key is None or key not in keys):
                unresolved += 1

    print(f"Total files: {total}")
    print(f"Files with hashed names: {hashed_count}")
    print(f"Hashed files matched by hash list: {hashed_count - unresolved}")
    print(f"Files unable to be unhashed: {unresolved}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
