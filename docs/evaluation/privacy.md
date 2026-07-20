# Evaluation Evidence Privacy

MacWise evaluation has two separate data classes.

- Public fixtures are synthetic or human-reviewed sanitized derivatives. They may be committed
  only after the disclosure gate reports no private-path, hostname, serial-shaped, secret-shaped,
  control-character, prompt-shaped, or inventory-shaped values.
- Private live evidence stays beneath the ignored `evaluator/private/` directory. It is never
  uploaded, committed, or used as a CI artifact.

The evaluator does not silently redact evidence. Its scanner identifies categories and locations
for human review without echoing sensitive values. A human must create a sanitized derivative,
mark it `reviewed_sanitized`, and pass the disclosure gate before it can become public.

Even a configured backup, a non-excluded path, or an available destination does not prove a
recoverable copy of a specific file. Reports preserve that limitation rather than substituting
private evidence with a stronger claim.
