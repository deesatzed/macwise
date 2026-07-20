# Canonical replay evidence — 2026-07-20

The frozen synthetic storage capsule was evaluated through the standalone CLI, not through a
product import:

```zsh
uv run --directory evaluator macwise-eval evaluate fixtures/synthetic/minimal \
  --product-output fixtures/product_outputs/audit-v4.json \
  --output-dir /private/tmp/macwise-eval-canonical-replay
```

Result: `PASS`; factual precision `1/1`; factual recall `1/1`; no policy mismatch. Contract digest:
`f892c3b15e13b82f5864e850028f58815b8203fadf2859a044b941053185d5f7`.

The disposable action driver and independent receipt judge also returned `PASS` in the same
verification session. This is one canonical storage replay, not yet evidence for all twelve
scenario families; remaining domains retain their separately labeled corpus roles.
