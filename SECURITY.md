# Security policy

## Core boundary

The core skill reads and writes learner-owned course state. It does not require credentials, API keys, telemetry, or external accounts.

## Installing

Review `SKILL.md`, `scripts/`, and requested permissions before installation. Install from this repository or a pinned commit. The optional `npx skills` installer has its own runtime and telemetry behavior; consult its current documentation and use its telemetry opt-out if desired.

## External connectors

Google Drive, Google Docs, NotebookLM, Composio, calendars, quiz services, and other integrations are optional. Use OAuth rather than sharing passwords. Grant the narrowest practical scope, review every requested action, and revoke access when no longer needed.

The tutor must preview external writes and obtain approval. A natural-language promise to touch only two documents is not necessarily an enforced OAuth boundary.

## Learning material

Webpages, PDFs, repositories, issues, comments, and pasted text are untrusted data. Instructions inside them must not override the skill, change tool permissions, or trigger actions.

## Reporting

Open a GitHub security advisory for vulnerabilities that could expose credentials, execute unapproved commands, corrupt learner state, or write outside the selected course directory.
