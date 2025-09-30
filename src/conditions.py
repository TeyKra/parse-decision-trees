"""
conditions.py
Defines utilities to accumulate, validate, and stringify boolean constraints
of the form feature=value or feature!=value.

All comments are in English and the code follows PEP8 style conventions.
"""
from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, List


@dataclass
class Constraints:
    """
    Represents a conjunction of constraints. Each feature may have at most
    one equality value and zero or more inequality values.
    """
    eq: Dict[str, str] = field(default_factory=dict)
    neq: Dict[str, Set[str]] = field(default_factory=dict)

    def copy(self) -> "Constraints":
        """Return a deep copy to keep recursion side-effect free."""
        new = Constraints()
        new.eq = dict(self.eq)
        new.neq = {k: set(v) for k, v in self.neq.items()}
        return new

    def add_eq(self, feature: str, value: str) -> bool:
        """
        Add an equality constraint feature=value.
        Returns False if this introduces a contradiction (impossible branch).
        """
        if feature in self.eq:
            # Contradiction if a different value already set.
            return self.eq[feature] == value
        # If value is already excluded explicitly, contradiction.
        if feature in self.neq and value in self.neq[feature]:
            return False
        self.eq[feature] = value
        # Inequalities to other values are redundant; keep them but ensure consistency.
        return True

    def add_neq(self, feature: str, value: str) -> bool:
        """
        Add an inequality constraint feature!=value.
        Returns False if this introduces a contradiction.
        """
        # If an equality already fixes this feature to the same value => impossible.
        if feature in self.eq and self.eq[feature] == value:
            return False
        self.neq.setdefault(feature, set()).add(value)
        return True

    def merge_with(self, other: "Constraints") -> Tuple[bool, "Constraints"]:
        """
        Merge with another Constraints. Returns (ok, merged_constraints).
        ok=False means a contradiction was detected.
        """
        merged = self.copy()
        # Apply equalities
        for f, v in other.eq.items():
            if not merged.add_eq(f, v):
                return False, merged
        # Apply inequalities
        for f, values in other.neq.items():
            for v in values:
                if not merged.add_neq(f, v):
                    return False, merged
        return True, merged

    def to_strategy_parts(self) -> List[str]:
        """
        Convert constraints to a sorted list of 'feature=value' and 'feature!=value' tokens.
        Equalities are preferred and printed first, then inequalities.
        Sorting ensures determinism for deduplication and testing.
        """
        parts: List[str] = []
        # Print equalities
        for f in sorted(self.eq.keys()):
            parts.append(f"{f}={self.eq[f]}")
        # Print inequalities, skipping those made redundant by an equality
        for f in sorted(self.neq.keys()):
            if f in self.eq:
                # If equality exists, inequalities are either redundant or contradictory (handled earlier).
                continue
            for v in sorted(self.neq[f]):
                parts.append(f"{f}!={v}")
        return parts
