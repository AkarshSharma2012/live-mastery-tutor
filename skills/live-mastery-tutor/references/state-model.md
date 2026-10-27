# State model and recovery

The learner state is the authority. Chat history is context, not durable evidence.

## Local course directory

```text
Learning/<course>/
├── course.json
├── learner.json
├── state.json
├── notes.md
├── sources.md
├── sessions/
└── evidence/
```

`course.json` defines objectives. `learner.json` stores learning preferences, goals, time budget, and storage mode. `state.json` stores assessed evidence and due reviews. `notes.md` is a compact learner-facing reference. Session and evidence files are append-only records.

## Topic status

- `not_started`: no instruction or evidence
- `introduced`: instruction delivered, no qualifying evidence yet
- `learning`: at least one evidence gate attempted
- `reviewing`: immediate gates passed; delayed reviews pending
- `mastered`: every applicable gate passed

Never infer a higher status from elapsed time, notes written, or lessons delivered.

## Evidence event

```json
{
  "topic_id": "D1.1",
  "kind": "teach_back",
  "result": "independent_correct",
  "score": null,
  "prompted": false,
  "observed": "Learner's relevant words or task output",
  "misconception": null
}
```

Kinds are `diagnostic`, `teach_back`, `hands_on`, `quiz`, `contrast`, and `review`. Preserve the first attempt separately from corrections.

## Review scheduling

Default successful-review intervals are 1, 3, 7, 14, 30, 60, and 120 days. An incorrect result returns the next review to one day. A prompted result does not advance the successful-review count. Course packs may override this.

Use dates as scheduling aids, not guilt. A missed date leaves the review due; it does not mark the learner behind or erase progress.

## Recovery

- State writes must use a temporary file followed by atomic replacement.
- `begin` creates a session lock. A second `begin` must refuse while the lock is live.
- `close` validates the session ID and evidence before updating state.
- If the process stops after real evidence but before close, reconstruct only from observable transcript or saved evidence. Mark reconstructed events and never award delayed-review credit.
- If no evidence occurred, cancel the abandoned session without advancing anything.

## Chat-only capsule

When files and writable documents are unavailable, output a fenced JSON block labeled `TUTOR_STATE_CAPSULE`. It must contain course version, objective statuses, raw recent evidence, active misconceptions, due reviews, next action, and a checksum-like stable course ID. Warn the learner to save it. Resume only from the newest capsule.
