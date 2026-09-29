# Contributing to Apistra

Apistra is being built in public, but external code contributions are not accepted during the 0.x foundation phase. This keeps architectural decisions, licensing, and the bootstrap evidence under one accountable maintainer group.

You may open a bug report or a discussion. Please do not submit pull requests unless an Apistra maintainer has explicitly invited the contribution. Unsolicited pull requests may be closed without review.

Never include secrets, personal data, customer data, or vulnerability details in a public issue. Follow [SECURITY.md](SECURITY.md) for security reports.

The intended protected flow is `feature/*` → `test` → `staging` → `main`. Deployment is always a separate manual operation and is never triggered automatically by a branch update.
