"""
tree_parser.py
Parses a textual OR-only decision tree into a dictionary of nodes.

Expected input line formats:
- "<id>:[cond1||or||cond2||or||...condK] yes=<id>,no=<id>"
- "<id>:leaf=<float_value>"

Each condition is "feature=value" (no spaces). Only "=" appears in the source;
negations are created during flattening for "no" branches.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class Node:
    node_id: int
    # Disjunctive conditions. Each is a (feature, value) tuple meaning feature=value.
    disjuncts: Optional[List[Tuple[str, str]]]  # None for leaves
    yes_id: Optional[int]  # child id when the OR condition is True
    no_id: Optional[int]   # child id when the OR condition is False
    leaf_value: Optional[float]  # not None for leaves


def parse_condition(token: str) -> Tuple[str, str]:
    """
    Parse "feature=value" into (feature, value).
    Feature names contain only letters; values may include digits, letters, ':' and 'x'.
    """
    if "=" not in token:
        raise ValueError(f"Invalid condition token: {token}")
    feature, value = token.split("=", 1)
    return feature.strip(), value.strip()


def parse_tree(path: str) -> Dict[int, Node]:
    nodes: Dict[int, Node] = {}
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            # Split id and rest
            try:
                left, right = line.split(":", 1)
            except ValueError:
                raise ValueError(f"Invalid line (missing ':'): {line}")
            node_id = int(left.strip())
            right = right.strip()
            if right.startswith("leaf="):
                # Leaf line
                val = float(right.split("=", 1)[1])
                nodes[node_id] = Node(node_id, None, None, None, val)
            else:
                # Internal OR node: "[...]" then "yes=,no="
                # Extract bracket content
                lb = right.find("[")
                rb = right.find("]")
                if lb == -1 or rb == -1 or rb < lb:
                    raise ValueError(f"Invalid node syntax: {line}")
                cond_block = right[lb + 1: rb]
                # Parse disjuncts separated by '||or||'
                cond_tokens = [t.strip() for t in cond_block.split("||or||")]
                disjuncts = [parse_condition(tok) for tok in cond_tokens if tok]
                # Parse children
                after = right[rb + 1:].strip()
                # Format expected: yes=<id>,no=<id>
                if not after.startswith("yes=") or ",no=" not in after:
                    raise ValueError(f"Invalid children syntax: {line}")
                yes_str, no_str = after.split(",no=")
                yes_id = int(yes_str.split("=", 1)[1])
                no_id = int(no_str.strip())
                nodes[node_id] = Node(node_id, disjuncts, yes_id, no_id, None)
    return nodes
