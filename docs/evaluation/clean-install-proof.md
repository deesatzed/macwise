# Clean evaluator installation proof

Date: 2026-07-20. A fresh UV tool environment installed the evaluator directly from the isolated
`evaluator/` project into a disposable local directory. The installed executable reported
`MacWise Evaluator 0.1.0.dev0`; `capture --help` and `evaluate --help` both rendered successfully.

This proves the evaluator's command surface installs without the product package. It is a local
tool-install proof, not publication to PyPI or Homebrew.
