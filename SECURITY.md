# Security Policy

## Supported versions

MacWise is release-candidate software. Security fixes are applied to the latest commit
and newest published pre-release only. Review the matching acceptance audit before using
cleanup features; RC status is not a production-safety certification.

## Report a vulnerability

Do not open a public issue for a vulnerability that could expose local inventory, execute discovered metadata, bypass approval, target protected software, or cause data loss.

Use the repository's private GitHub security-advisory reporting flow. Include:

- the affected version or commit,
- the smallest safe reproduction,
- expected and observed behavior,
- whether any installed software or user data changed,
- suggested mitigations, if known.

Do not include real secrets, private keys, full software inventories, or unnecessary personal paths. Use synthetic names and fixtures whenever possible.

## Response expectations

Maintainers will acknowledge a valid private report, reproduce it safely, assess impact,
and coordinate remediation and disclosure. Exact response times are not promised during
the release-candidate period.

## Safety boundary

Audit and review operations must remain read-only. Any future mutation must use a reviewed plan, unambiguous target, allowlisted executor, action-time approval, rollback manifest, post-action verification, and documented undo behavior.

Release automation must use pinned actions, least privilege, exact version/tag matching,
and PyPI trusted publishing. Never place package or tap credentials in issues, fixtures,
workflow source, or audit output.
