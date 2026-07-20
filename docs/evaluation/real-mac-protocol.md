# Private Real-Mac Evaluation Protocol

This protocol creates evidence for one exact Mac environment. It does not prove behavior on every
Mac, and it does not upload or publish the inventory.

1. Create a new empty directory beneath the ignored `evaluator/private/` directory.
2. Run `macwise-eval capture --private-output PATH` to collect independent read-only receipts.
3. Immediately run the installed product with explicit JSON output in the same private directory.
4. Record the product version, audit schema, capture time, macOS product version/build, Darwin
   version, architecture, and tool versions.
5. Add a scenario oracle before inspecting the product result. Mark the capsule `fresh_holdout`.
6. Run the evaluator. If the outcome changes either product or evaluator code, retire the capsule
   to `development`; a new holdout is then required for a new generalization claim.
7. Inspect every critical or unsupported verdict. Create only an aggregate sanitized report for
   Git, then run the disclosure scanner before committing it.

The protocol is read-only through collection and evaluation. Disposable action-lab tests are a
separate procedure and must never use applications, Homebrew packages, services, startup items,
or data that belong to the real Mac.
