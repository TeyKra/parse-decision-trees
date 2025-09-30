"""
main.py
Entry point: parse the tree file, flatten it, and write strategies.txt.

Usage:
    python main.py --tree tree_to_convert.txt --output strategies.txt
"""

import argparse
from tree_parser import parse_tree
from flattener import flatten_tree
from io_utils import write_strategies


def main(tree_path: str, output_path: str) -> int:
    """Parse the tree, flatten it, and write strategies to output file."""
    nodes = parse_tree(tree_path)
    strategies = flatten_tree(nodes, root_id=0)

    with open(output_path, "w", encoding="utf-8") as out:
        written = write_strategies(strategies, out)

    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Flatten an OR-only decision tree into strategies."
    )
    parser.add_argument(
        "--tree", required=True, help="Path to the input tree file (tree_to_convert.txt)"
    )
    parser.add_argument(
        "--output", required=True, help="Path to the output strategies file"
    )

    args = parser.parse_args()
    n = main(args.tree, args.output)
    print(f"Wrote {n} strategies to {args.output}")
