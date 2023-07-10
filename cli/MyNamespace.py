from argparse import Namespace
from pathlib import Path


class MyNamespace(Namespace):
    to_move: Path | list[Path]
    move_to: Path
