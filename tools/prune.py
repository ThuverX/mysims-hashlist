#!/usr/bin/env python3
"""Keep hash-list entries whose hashed or unhashed filename is in a game folder."""

import argparse
import os
from pathlib import Path
import re
import sys

HASHED_NAME = re.compile(r"^(0x[0-9a-f]+!0x[0-9a-f]+)(\..+)$")


def load_type_ids(path):
    """Read lines of the form ``0xTYPE extension``; // starts a comment."""
    types = {}
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        fields = line.split("//", 1)[0].split()
        if not fields:
            continue
        if len(fields) != 2 or not re.fullmatch(r"0[xX][0-9a-fA-F]{1,8}", fields[0]):
            raise ValueError(f"Invalid file association on line {number}: {line}")
        extension = "." + fields[1].lstrip(".").casefold()
        if extension == "." or "/" in extension or "\\" in extension:
            raise ValueError(f"Invalid extension on line {number}: {fields[1]}")
        type_id = int(fields[0], 16)
        if extension in types and types[extension] != type_id:
            raise ValueError(f"Conflicting file association on line {number}: {fields[1]}")
        types[extension] = type_id
    return types


def fnv32(text):
    value = 0x811c9dc5
    for byte in text.lower().encode("utf-8"):
        value = ((value * 0x01000193) & 0xffffffff) ^ byte
    return value


def canonical_hash(name, type_ids):
    """Normalize a hashed filename, including its textual or numeric type."""
    match = HASHED_NAME.fullmatch(name.casefold())
    if not match:
        return None
    prefix, extension = match.groups()
    group, instance = prefix.split("!")
    if extension.startswith(".0x"):
        try:
            type_id = int(extension[1:], 16)
        except ValueError:
            return None
    else:
        type_id = type_ids.get(extension)
        if type_id is None:
            type_id = fnv32(extension)
    return int(group, 16), int(instance, 16), type_id


def scan_names(folder, type_ids):
    names = set()
    hashes = set()

    def fail(error):
        raise error

    for _, _, files in os.walk(folder, onerror=fail):
        for name in files:
            names.add(name.casefold())
            key = canonical_hash(name, type_ids)
            if key is not None:
                hashes.add(key)
    return names, hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hashlist", type=Path, help="Input hash list")
    parser.add_argument("game_folder", type=Path, help="Game data folder")
    parser.add_argument("file_types", type=Path, help="File associations (DDFMap.txt)")
    args = parser.parse_args()
    if not args.game_folder.is_dir():
        parser.error(f"Not a directory: {args.game_folder}")

    type_ids = load_type_ids(args.file_types)
    names, hashes = scan_names(args.game_folder, type_ids)
    lines = args.hashlist.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    kept = []
    for number, line in enumerate(lines, 1):
        fields = line.strip().split(maxsplit=1)
        if len(fields) != 2:
            raise ValueError(f"Invalid hash-list entry on line {number}: expected two names")
        hashed, unhashed = fields
        key = canonical_hash(hashed, type_ids)
        if hashed.casefold() in names or unhashed.casefold() in names or (key is not None and key in hashes):
            kept.append(line)

    output = Path(str(args.hashlist) + ".pruned")
    output.write_text("".join(kept), encoding="utf-8", newline="")
    print(f"Kept {len(kept)} of {len(lines)} entries in {output}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
