"""
validator.py
Replay each strategy against the OR-only tree to ensure it deterministically
reaches the correct leaf with the exact leaf value.

Usage:
  python validator.py --tree /path/tree_to_convert.txt --strategies /path/strategies.txt

Exit codes:
  0 = all strategies validated
  1 = validation failures occurred
  2 = I/O or parsing error
"""
import argparse
import math
from typing import Dict, List, Tuple, Set, Optional

# Local imports (files expected in the same folder or on PYTHONPATH)
from tree_parser import parse_tree


def parse_strategy_line(line: str) -> Tuple[Dict[str, str], Dict[str, Set[str]], float]:
    """
    Parse a line of the form:
        "a=1 & b!=2 & c=3 : 0.0123"
    We split on the LAST colon in case some values contain ':' (e.g. region=FR:A5).
    Returns (eq, neq, leaf_value).
    """
    try:
        lhs, rhs = line.rsplit(":", 1)
    except ValueError as e:
        raise ValueError(f"Strategy line has no ':' separator: {line}") from e
    leaf = float(rhs.strip())
    lhs = lhs.strip()
    eq: Dict[str, str] = {}
    neq: Dict[str, Set[str]] = {}

    if lhs != "TRUE" and lhs != "":
        parts = [p.strip() for p in lhs.split("&")]
        for p in parts:
            if not p:
                continue
            if "!=" in p:
                f, v = p.split("!=", 1)
                f, v = f.strip(), v.strip()
                if not f:
                    raise ValueError(f"Empty feature in token: {p}")
                neq.setdefault(f, set()).add(v)
            elif "=" in p:
                f, v = p.split("=", 1)
                f, v = f.strip(), v.strip()
                if not f:
                    raise ValueError(f"Empty feature in token: {p}")
                eq[f] = v
            else:
                raise ValueError(f"Invalid token (expected '=' or '!='): {p}")
    return eq, neq, leaf


def decide_branch(disjuncts: List[Tuple[str, str]],
                  eq: Dict[str, str],
                  neq: Dict[str, Set[str]]) -> Optional[bool]:
    """
    Decide which branch to take for an OR node given constraints.
    Return True for 'yes', False for 'no', None if undetermined.
    - yes if ANY disjunct (feature=value) is forced True by constraints
    - no if ALL disjuncts are forced False by constraints
    - None otherwise
    """
    forced_true = False
    all_forced_false = True

    for f, v in disjuncts:
        # Forced True?
        if f in eq and eq[f] == v:
            forced_true = True

        # Forced False?
        this_false = False
        if f in eq and eq[f] != v:
            this_false = True
        if f in neq and v in neq[f]:
            this_false = True
        if not this_false:
            all_forced_false = False

    if forced_true:
        return True
    if all_forced_false:
        return False
    return None


def validate(tree_path: str, strategies_path: str, atol: float = 1e-9) -> int:
    """
    Validate all strategies. Returns the number of failures.
    Prints a detailed report.
    """
    nodes = parse_tree(tree_path)

    with open(strategies_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    failures = []
    ok = 0
    leaf_hits: Dict[int, int] = {}

    for idx, line in enumerate(lines, 1):
        try:
            eq, neq, strat_leaf = parse_strategy_line(line)
        except Exception as e:
            failures.append((idx, line, f"Parse error: {e}"))
            continue

        current_id = 0
        safety = 0
        while True:
            node = nodes[current_id]
            if node.leaf_value is not None:
                if not math.isclose(node.leaf_value, strat_leaf, rel_tol=0.0, abs_tol=atol):
                    failures.append(
                        (idx, line,
                         f"Leaf mismatch: reached leaf #{current_id} value {node.leaf_value} "
                         f"but strategy encodes {strat_leaf}")
                    )
                else:
                    ok += 1
                    leaf_hits[current_id] = leaf_hits.get(current_id, 0) + 1
                break

            decision = decide_branch(node.disjuncts, eq, neq)
            if decision is True:
                current_id = node.yes_id
            elif decision is False:
                current_id = node.no_id
            else:
                failures.append((idx, line, "Undetermined branch: constraints do not force yes nor no."))
                break

            safety += 1
            if safety > 100000:
                failures.append((idx, line, "Traversal too deep / cycle suspected."))
                break

    total = len(lines)
    print(f"Validation summary: {ok}/{total} strategies validated.")
    if failures:
        print("\nFailures:")
        for i, (lineno, text, reason) in enumerate(failures, 1):
            print(f"{i}. line #{lineno}: {text}")
            print(f"   -> {reason}")
    else:
        print("No failures.")

    # Coverage report
    all_leaf_ids = sorted(nid for nid, n in nodes.items() if n.leaf_value is not None)
    covered = sorted(leaf_hits.keys())
    missed = [lid for lid in all_leaf_ids if lid not in leaf_hits]
    print("\nLeaf coverage:")
    print(f"Covered leaves: {covered}")
    print(f"Missed leaves: {missed}")
    print(f"Hit count per leaf: {leaf_hits}")

    return len(failures)


def main():
    p = argparse.ArgumentParser(description="Validate flattened strategies against an OR-only tree.")
    p.add_argument("--tree", required=True, help="Path to tree_to_convert.txt")
    p.add_argument("--strategies", required=True, help="Path to strategies.txt")
    p.add_argument("--atol", type=float, default=1e-9, help="Absolute tolerance for float comparison")
    args = p.parse_args()

    try:
        failures = validate(args.tree, args.strategies, atol=args.atol)
    except FileNotFoundError as e:
        print(f"I/O error: {e}")
        raise SystemExit(2)
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise SystemExit(2)

    raise SystemExit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
