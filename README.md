# Tree to Strategies Converter

## Exercise Description

The objective of this project is to **flatten a condition tree** (provided as `tree_to_convert.txt`) into a set of **strategies**.

A **strategy** is defined as:  
- A sequence of conditions of the form `{feature} = {value}` or `{feature} != {value}` separated with `and`.  
- Followed by a **leaf value**.

### Syntax of a strategy
```
{strategy definition} : {leaf_value}
```

#### Example
```
device_type!=pc & browser!=7 & browser=8 : 0.000881108
```

### Constraints
- The script must be written in Python.
- It must take `tree_to_convert.txt` as input and output the flattened strategies into `strategies.txt`.
- The solution must be **generic** and applicable to any tree of the same structure.

### Assumptions
- Only OR conditions are present.
- Only `=` and `!=` operators are used.
- Variable names consist of letters only.
- Tree depth may vary.

### Bonus Requirements
- The script should avoid generating **impossible strategies** (contradictory conditions).
- Strategies must be **simplified** where possible:  
  Example: `value=4` is preferred over `value!=3 & value=4`.
- Memory complexity must be less than **O(n)**, meaning the memory footprint should remain below the input file size.

---

## Methodology

### 1. Problem Analysis
The challenge is to transform a condition tree into a **list of valid and simplified strategies**.  
Each path from the root to a leaf corresponds to one strategy.

Key requirements:  
- Avoid contradictions.  
- Simplify redundant conditions.  
- Generate strategies efficiently in a streaming fashion.

---

### 2. Modular Design
The project was designed with **modularity** in mind:

- **`tree_parser.py`**: Parses the input file into a structured tree.  
- **`conditions.py`**: Handles conditions, including simplification and contradiction detection.  
- **`flattener.py`**: Performs a recursive Depth-First Search (DFS) to generate strategies.  
- **`io_utils.py`**: Manages file reading and writing.  
- **`main.py`**: Entry point using `argparse` for CLI arguments.  
- **`validator.py`**: Validates the generated strategies against the original tree.

---

### 3. Tree Parsing
The tree is represented in two possible formats:
- **OR-node**:  
  ```
  id:[cond1||cond2] yes=<id>,no=<id>
  ```
- **Leaf-node**:  
  ```
  id:leaf=<float>
  ```

The parser converts these lines into a dictionary of `Node` objects with conditions, branches, and values.

---

### 4. Flattening Logic
A **Depth-First Search (DFS)** traversal is used:
1. Start at the root with an empty condition path.  
2. Add conditions at each node.  
3. Detect contradictions and discard invalid paths.  
4. At a leaf, output the concatenated conditions followed by the leaf value.  

The process uses `yield` to **stream strategies directly to the output file**, ensuring low memory usage.

---

### 5. Condition Simplification
Simplification rules are applied during traversal:
- When an equality (`feature=value`) is encountered, all previous inequalities (`feature!=...`) for the same feature are removed.  
- This guarantees **minimal and clear strategies**.

---

### 6. Writing Results
Strategies are written to `strategies.txt` using a **streaming approach**:
- No full list of strategies is kept in memory.  
- Memory usage stays below **O(n)**.

---

### 7. Validation
The `validator.py` module ensures correctness by:
- Replaying each strategy on the original tree.  
- Verifying that the leaf value matches.  
- Reporting coverage and contradictions.  

It provides a CLI with options for tolerance (`--atol`) and safeguards against infinite recursion.

---

## How to Run

### Generate Strategies
```bash
python src/main.py --tree tree_to_convert.txt --output strategies.txt
```

### Validate Strategies
```bash
python src/validator.py --tree tree_to_convert.txt --strategies strategies.txt
```

