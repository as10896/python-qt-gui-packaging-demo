"""Core logic: rename files to random UUIDs. Also usable as a CLI:

    python renamer.py photo.jpg some-folder/
"""

import sys
from pathlib import Path
from uuid import uuid4


def rename_to_uuid(path: Path) -> Path:
    """Rename a file to `<uuid4><original suffix>` and return the new path."""
    new_path = path.with_name(f"{uuid4()}{path.suffix}")
    path.rename(new_path)
    return new_path


def expand(paths):
    """Yield files from the given paths. Folders are expanded one level deep,
    skipping hidden files such as .DS_Store."""
    for path in map(Path, paths):
        if path.is_dir():
            yield from sorted(
                f for f in path.iterdir() if f.is_file() and not f.name.startswith(".")
            )
        elif path.is_file():
            yield path


if __name__ == "__main__":
    # Materialize the list first so we don't rename while iterating a folder
    for f in list(expand(sys.argv[1:])):
        print(f"{f.name}  ->  {rename_to_uuid(f).name}")
