# Live Mastery Tutor

An open, portable Agent Skill for adaptive tutoring with durable state, honest assessment, hands-on practice, and spaced retrieval.

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-5B5BD6)](https://agentskills.io/specification)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

The model teaches; the state engine remembers what the learner actually demonstrated. The skill works for exams, technical tools, school subjects, source collections, and repository walkthroughs. A current GitHub Foundations GH-900 course pack is included.

## Install with one prompt

Paste this into Codex, Claude Code, Cursor, Antigravity, or another agent that can run commands:

```text
Set up Live Mastery Tutor from https://github.com/AkarshSharma2012/live-mastery-tutor and start an isolated tutoring course for me.

1. Review the repository's README, SKILL.md, requested permissions, and scripts before installing anything.
2. If this agent supports Agent Skills and Node.js 22.20+ is available, run:
   npx skills add AkarshSharma2012/live-mastery-tutor --skill live-mastery-tutor -g -y
3. Otherwise, use the repository's skills/live-mastery-tutor/SKILL.md and referenced files directly for this project without modifying unrelated agent settings.
4. Prefer local state in ./Learning. If durable local files are unavailable, offer connected-document mode; otherwise use the chat-only state capsule.
5. Do not connect accounts, install extra integrations, or create external writes without asking me first.
6. Ask what I want to learn, why, my current level, available time, and deadline. Then diagnose me one question at a time, show a tailored course map, and wait for approval before Lesson 1.
7. If I choose GitHub Foundations, use the included current GH-900 course pack and verify its official blueprint before teaching.
```

For a project-only install, remove `-g`. To choose a specific agent non-interactively, add the current `skills` CLI agent flag shown by `npx skills add --help`.

## ChatGPT or Claude web without local skill installation

Create a separate Project/chat and paste the same prompt. The assistant should use the repository instructions in chat-only mode and return a complete `TUTOR_STATE_CAPSULE` at each session close. Web chats cannot be assumed to install files, run Python, schedule themselves, or update external documents.

## What makes the workflow different

- **Evidence-gated mastery:** being taught is not being mastered.
- **First-attempt honesty:** corrections never overwrite the original score.
- **Teach-back plus authentic work:** recognition alone is insufficient.
- **Spaced and interleaved retrieval:** reviews are scheduled and questions must be novel.
- **Deterministic state:** a standard-library Python tool atomically records progress and refuses mismatched sessions.
- **Crash recovery:** state lives outside the conversation and can survive a fresh agent or compacted chat.
- **Three storage modes:** local files, connected documents, or a portable state capsule.
- **Source grounding:** course maps point to authoritative material and track freshness.
- **Safe integrations:** external writes require exact targets, previews, approval, and verification.
- **Course packs:** reusable objective maps can be versioned independently of learner progress.

## Included GH-900 pack

The GitHub Foundations pack is based on the official Microsoft Learn blueprint marked “skills at a glance as of January 2026” and was rechecked on October 27, 2026. It includes all seven domains, weights, objective IDs, hands-on flags, and common concept confusions.

Initialize it manually:

```powershell
python skills/live-mastery-tutor/scripts/tutor_state.py init `
  --root Learning/github-foundations `
  --course-pack skills/live-mastery-tutor/assets/course-packs/github-foundations-gh900.json `
  --goal "Pass GH-900 and use GitHub independently" `
  --minutes 45
```

Start a session:

```powershell
python skills/live-mastery-tutor/scripts/tutor_state.py begin `
  --root Learning/github-foundations `
  --minutes 45
```

The agent teaches from the returned brief and closes with a structured evidence file. Run `--help` for the complete interface.

## Repository layout

```text
skills/live-mastery-tutor/
├── SKILL.md
├── agents/openai.yaml
├── scripts/tutor_state.py
├── references/
└── assets/
    ├── course-packs/
    └── templates/
```

## Design research

The skill follows the [Agent Skills specification](https://agentskills.io/specification) and progressive disclosure guidance. Its teaching loop applies retrieval practice, spacing, interleaving, elaboration, concrete examples, calibration, and evidence-based mastery gates.

The design was informed by public tutor projects including [Aristotle](https://github.com/Haseeb-Qureshi/aristotle) and [agent-tutor](https://github.com/Mohamed-El-Sharqawy/agent-tutor). Live Mastery Tutor is an independent implementation with a smaller portable core, explicit cross-surface fallback modes, exam-blueprint course packs, and a deterministic evidence ledger.

## Security

Read [SECURITY.md](SECURITY.md) before enabling external connectors. The core requires no account connection, API key, or network access. Review third-party skills before installation and pin a commit when reproducibility matters.

## License

MIT
