# Disposable action-lab protocol

This is the only evaluation exercise that uses product apply or undo behavior. It never selects
or modifies installed software.

Run it from the product checkout with an explicit, empty output directory:

```zsh
uv run python scripts/run_action_lab.py --output-dir /private/tmp/macwise-action-lab-receipt
uv run --directory evaluator python -c 'import json; from pathlib import Path; from macwise_eval.action_lab import evaluate_action_lab; print(evaluate_action_lab(json.loads(Path("/private/tmp/macwise-action-lab-receipt/action-lab.json").read_text())))'
```

The driver creates a fresh temporary directory below `/private/tmp`, containing only a synthetic
application bundle, a temporary Trash directory, state databases, and an unrelated sentinel file.
It plans and applies one synthetic move, intentionally loses post-restore evidence during undo to
exercise recovery, then completes undo. The temporary directory is removed on exit.

The saved receipt contains booleans, lifecycle states, and payload hashes only. It contains no
real app names, account paths, or temporary paths. The evaluator accepts it only when it proves:

- the synthetic source existed before apply;
- apply moved that source to the temporary Trash;
- interrupted recovery restored the source;
- final undo restored the original payload and removed the temporary Trash copy;
- the unrelated sentinel remained unchanged; and
- the journal ended as `succeeded` then `undone`.

A missing field or mismatched hash is a failed safety proof, never a pass by default.
