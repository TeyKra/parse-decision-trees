"""
flattener.py
Flattens an OR-only decision tree into concrete strategies.

Now preserves the *traversal order* of constraints exactly as encountered
in the tree, instead of alphabetically sorting them.
"""
from typing import Dict, Iterable, List, Tuple, Set
from conditions import Constraints
from tree_parser import Node


def _append_token(path_tokens: List[str], token: str) -> None:
    """Append a token to the path if not already present at the tail position."""
    if not path_tokens or path_tokens[-1] != token:
        path_tokens.append(token)


def _remove_neq_tokens_for_feature(path_tokens: List[str], feature: str) -> None:
    """Remove previously added 'feature!=*' tokens when we later assert 'feature=...'."""
    keep: List[str] = []
    prefix = feature + "!="
    for t in path_tokens:
        if not t.startswith(prefix):
            keep.append(t)
    path_tokens[:] = keep


def _dfs(nodes: Dict[int, Node],
         node_id: int,
         acc: Constraints,
         path_tokens: List[str]) -> Iterable[Tuple[List[str], float]]:
    """
    Depth-first traversal generating (ordered_tokens, leaf_value) pairs.
    - ordered_tokens preserves the exact order constraints were encountered.
    - acc provides contradiction checks and minimality rules.
    """
    node = nodes[node_id]
    if node.leaf_value is not None:
        yield list(path_tokens), node.leaf_value
        return

    assert node.disjuncts is not None

    # Branch YES: pick ONE disjunct to assert true (minimal sufficient condition)
    for feature, value in node.disjuncts:
        child_acc = acc.copy()
        if child_acc.add_eq(feature, value):
            child_tokens = list(path_tokens)
            _remove_neq_tokens_for_feature(child_tokens, feature)
            _append_token(child_tokens, f"{feature}={value}")
            yield from _dfs(nodes, node.yes_id, child_acc, child_tokens)

    # Branch NO: all disjuncts must be false (add 'feature!=value' for each)
    child_acc = acc.copy()
    child_tokens = list(path_tokens)
    ok = True
    for feature, value in node.disjuncts:
        if feature in child_acc.eq:
            if not child_acc.add_neq(feature, value):
                ok = False
                break
            continue
        if not child_acc.add_neq(feature, value):
            ok = False
            break
        _append_token(child_tokens, f"{feature}!={value}")
    if ok:
        yield from _dfs(nodes, node.no_id, child_acc, child_tokens)


def flatten_tree(nodes: Dict[int, Node], root_id: int = 0) -> Iterable[Tuple[List[str], float]]:
    """
    Flatten the tree rooted at root_id.
    Returns an iterable of (ordered_tokens, leaf_value) where ordered_tokens preserves
    the real traversal order (no alphabetical sorting).
    """
    seen: Set[Tuple[Tuple[str, str], float]] = set()
    for tokens, leaf in _dfs(nodes, root_id, Constraints(), []):
        # Deduplication key: sort tokens internally for uniqueness check
        eq = sorted(t for t in tokens if "!=" not in t)
        neq = sorted(t for t in tokens if "!=" in t)
        key = (tuple(eq + neq), leaf)
        if key in seen:
            continue
        seen.add(key)
        yield tokens, leaf
