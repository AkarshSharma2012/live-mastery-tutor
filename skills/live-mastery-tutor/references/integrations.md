# Optional integrations

The tutor works without external accounts. Integrations are convenience layers, never the authoritative evidence by default.

## Google Docs and NotebookLM

Recommended document roles:

1. **Mastery Tracker:** objective status, first-attempt scores, hands-on evidence, misconceptions, and review dates.
2. **Compact Notes:** durable concepts, distinctions, procedures, traps, and unresolved personal misconceptions.

NotebookLM can use these as sources for flashcards, quizzes, study guides, and audio overviews. Generated artifacts do not change mastery state.

Before a document write:

1. Resolve the exact document ID.
2. Read the current section.
3. Show the full proposed replacement or insertion.
4. Obtain explicit approval in the current conversation.
5. Execute once.
6. Read back and verify.

Never identify a write target by title alone after setup. Never delete a learning record. A prompt restriction to two documents is not necessarily an OAuth permission boundary.

## Composio or another action layer

Use the narrowest connected tool capable of the requested document operation. Discover and inspect the tool schema before executing. Connections may be isolated between a provider dashboard, hosted MCP, and local CLI; verify on the same surface the tutor will use.

Do not request or expose tokens. After a timeout or unclear write, read the destination before retrying. Never retry an uncertain write through a second integration surface.

## Flashcards and quiz tools

Export only eligible learned or due topics. Exclude `not_started`. Include objective IDs so results can be returned to the state model. External quiz scores count only when question scope, first attempts, and learner identity are clear.

## Schedulers

A reminder wakes the learner; it does not teach unattended. Schedule a short nudge containing the next-session hook. State advances only when the learner participates and evidence is recorded.

If the platform has no scheduler, provide a reusable start prompt instead of pretending a recurring job exists.
