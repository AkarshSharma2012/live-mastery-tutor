#!/usr/bin/env python3
"""Deterministic local state for Live Mastery Tutor.

The script stores evidence; it does not generate lessons or grade free-form answers.
Run with --help before use.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
REVIEW_INTERVALS = [1, 3, 7, 14, 30, 60, 120]
VALID_KINDS = {
    "diagnostic",
    "instruction",
    "teach_back",
    "hands_on",
    "quiz",
    "contrast",
    "review",
}
VALID_RESULTS = {
    "independent_correct",
    "prompted_correct",
    "incorrect",
    "observed",
    "not_applicable",
}


class TutorStateError(RuntimeError):
    pass


def today() -> dt.date:
    return dt.date.today()


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TutorStateError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TutorStateError(f"Invalid JSON in {path}: {exc}") from exc


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def course_topics(course: dict[str, Any]) -> dict[str, dict[str, Any]]:
    topics: dict[str, dict[str, Any]] = {}
    for domain in course.get("domains", []):
        for objective in domain.get("objectives", []):
            topic = dict(objective)
            topic["domain_id"] = domain["id"]
            topic["domain_title"] = domain["title"]
            if topic["id"] in topics:
                raise TutorStateError(f"Duplicate objective ID: {topic['id']}")
            topics[topic["id"]] = topic
    if not topics:
        raise TutorStateError("Course contains no objectives")
    return topics


def empty_topic_state(topic: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "not_started",
        "events": [],
        "teach_back": False,
        "hands_on": not bool(topic.get("hands_on", False)),
        "contrast": False,
        "best_quiz_first_attempt": None,
        "review_successes": 0,
        "next_review": None,
        "active_misconceptions": [],
    }


def load_root(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    course = read_json(root / "course.json")
    state = read_json(root / "state.json")
    topics = course_topics(course)
    if state.get("schema_version") != SCHEMA_VERSION:
        raise TutorStateError("Unsupported state schema version")
    missing = set(topics) - set(state.get("topics", {}))
    if missing:
        raise TutorStateError(f"State is missing objectives: {', '.join(sorted(missing))}")
    return course, state, topics


def cmd_init(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    if root.exists() and any(root.iterdir()) and not args.force:
        raise TutorStateError(f"Refusing to initialize non-empty directory: {root}")
    pack = Path(args.course_pack).resolve()
    course = read_json(pack)
    topics = course_topics(course)
    root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pack, root / "course.json")
    state = {
        "schema_version": SCHEMA_VERSION,
        "course_id": course["id"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "session_count": 0,
        "topics": {topic_id: empty_topic_state(topic) for topic_id, topic in topics.items()},
    }
    learner = {
        "goal": args.goal or course.get("default_goal", "Complete the course with durable mastery"),
        "state_mode": "local",
        "typical_minutes": args.minutes,
        "feedback_tone": "direct",
        "preferences": [],
    }
    atomic_json(root / "state.json", state)
    atomic_json(root / "learner.json", learner)
    (root / "sessions").mkdir(exist_ok=True)
    (root / "evidence").mkdir(exist_ok=True)
    (root / "notes.md").write_text(
        f"# {course['title']} — compact notes\n\nNo topics studied yet.\n",
        encoding="utf-8",
    )
    source_lines = [f"# {course['title']} — sources", ""]
    for source in course.get("sources", []):
        source_lines.append(f"- [{source['title']}]({source['url']}) — {source.get('kind', 'source')}")
    (root / "sources.md").write_text("\n".join(source_lines) + "\n", encoding="utf-8")
    return {"status": "initialized", "root": str(root), "objectives": len(topics)}


def is_due(topic_state: dict[str, Any], on: dt.date) -> bool:
    due = topic_state.get("next_review")
    return bool(due and dt.date.fromisoformat(due) <= on and topic_state["status"] != "mastered")


def cmd_begin(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    course, state, topics = load_root(root)
    lock_path = root / ".session.json"
    if lock_path.exists():
        lock = read_json(lock_path)
        raise TutorStateError(f"A session is already open: {lock.get('session_id', 'unknown')}")

    due = [topic_id for topic_id, value in state["topics"].items() if is_due(value, today())]
    unfinished = [
        topic_id
        for topic_id, value in state["topics"].items()
        if value["status"] in {"not_started", "introduced", "learning"}
    ]
    primary = due[0] if due else (unfinished[0] if unfinished else None)
    session_id = uuid.uuid4().hex[:12]
    lock = {
        "session_id": session_id,
        "opened_at": now_iso(),
        "minutes": args.minutes,
        "primary_topic": primary,
        "due_reviews": due[: min(3, len(due))],
    }
    atomic_json(lock_path, lock)
    return {
        "session_id": session_id,
        "course": course["title"],
        "minutes": args.minutes,
        "primary": {"id": primary, **topics[primary]} if primary else None,
        "due_reviews": [{"id": item, **topics[item]} for item in lock["due_reviews"]],
        "stop_when": "primary application and exit retrieval are graded, or time expires",
    }


def valid_score(value: Any) -> float | None:
    if value is None:
        return None
    score = float(value)
    if not 0 <= score <= 1:
        raise TutorStateError("Scores must be between 0 and 1")
    return score


def normalize_event(raw: dict[str, Any], topics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    topic_id = raw.get("topic_id")
    kind = raw.get("kind")
    result = raw.get("result")
    if topic_id not in topics:
        raise TutorStateError(f"Unknown topic_id: {topic_id}")
    if kind not in VALID_KINDS:
        raise TutorStateError(f"Invalid evidence kind: {kind}")
    if result not in VALID_RESULTS:
        raise TutorStateError(f"Invalid evidence result: {result}")
    event = {
        "topic_id": topic_id,
        "kind": kind,
        "result": result,
        "score": valid_score(raw.get("score")),
        "prompted": bool(raw.get("prompted", result == "prompted_correct")),
        "observed": str(raw.get("observed", "")).strip(),
        "misconception": raw.get("misconception"),
        "recorded_at": now_iso(),
        "reconstructed": bool(raw.get("reconstructed", False)),
    }
    if kind == "quiz" and event["score"] is None:
        raise TutorStateError("Quiz evidence requires score")
    if not event["observed"]:
        raise TutorStateError(f"Evidence for {topic_id} requires an observed description")
    return event


def update_topic(topic: dict[str, Any], current: dict[str, Any], event: dict[str, Any], threshold: float) -> None:
    current["events"].append(event)
    independent = event["result"] == "independent_correct" and not event["prompted"]
    if event["kind"] == "instruction" and current["status"] == "not_started":
        current["status"] = "introduced"
    elif event["kind"] != "instruction" and current["status"] in {"not_started", "introduced"}:
        current["status"] = "learning"

    if event["kind"] == "teach_back" and independent:
        current["teach_back"] = True
    if event["kind"] == "hands_on" and independent:
        current["hands_on"] = True
    if event["kind"] == "contrast" and independent:
        current["contrast"] = True
    if event["kind"] == "quiz":
        existing = current.get("best_quiz_first_attempt")
        current["best_quiz_first_attempt"] = max(existing or 0, event["score"])
    if event.get("misconception"):
        value = str(event["misconception"]).strip()
        if value and value not in current["active_misconceptions"]:
            current["active_misconceptions"].append(value)

    if event["kind"] == "review":
        if independent and not event["reconstructed"]:
            current["review_successes"] += 1
            index = min(current["review_successes"], len(REVIEW_INTERVALS) - 1)
            current["next_review"] = (today() + dt.timedelta(days=REVIEW_INTERVALS[index])).isoformat()
        else:
            current["next_review"] = (today() + dt.timedelta(days=1)).isoformat()

    quiz_ok = (current.get("best_quiz_first_attempt") or 0) >= threshold
    immediate = current["teach_back"] and current["hands_on"] and current["contrast"] and quiz_ok
    if immediate and current["review_successes"] >= 2:
        current["status"] = "mastered"
        current["next_review"] = None
    elif immediate:
        current["status"] = "reviewing"
        if not current.get("next_review"):
            current["next_review"] = (today() + dt.timedelta(days=1)).isoformat()


def cmd_close(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    course, state, topics = load_root(root)
    lock_path = root / ".session.json"
    lock = read_json(lock_path)
    payload = read_json(Path(args.evidence).resolve())
    if payload.get("session_id") != lock.get("session_id"):
        raise TutorStateError("Evidence session_id does not match the open session")
    raw_events = payload.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        raise TutorStateError("Evidence must contain at least one event")
    events = [normalize_event(item, topics) for item in raw_events]
    threshold = float(course.get("mastery_threshold", 0.8))
    for event in events:
        update_topic(topics[event["topic_id"]], state["topics"][event["topic_id"]], event, threshold)
    state["session_count"] += 1
    state["updated_at"] = now_iso()
    session_record = {
        **lock,
        "closed_at": now_iso(),
        "events": events,
        "summary": str(payload.get("summary", "")).strip(),
        "next_hook": str(payload.get("next_hook", "")).strip(),
    }
    session_path = root / "sessions" / f"{state['session_count']:04d}-{lock['session_id']}.json"
    atomic_json(session_path, session_record)
    atomic_json(root / "state.json", state)
    lock_path.unlink()
    mastered = sum(1 for value in state["topics"].values() if value["status"] == "mastered")
    return {
        "status": "closed",
        "session": state["session_count"],
        "events_recorded": len(events),
        "mastered": mastered,
        "total": len(topics),
        "session_record": str(session_path),
    }


def cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    course, state, topics = load_root(root)
    counts: dict[str, int] = {}
    for value in state["topics"].values():
        counts[value["status"]] = counts.get(value["status"], 0) + 1
    due = [topic_id for topic_id, value in state["topics"].items() if is_due(value, today())]
    return {
        "course": course["title"],
        "sessions": state["session_count"],
        "counts": counts,
        "due": due,
        "total": len(topics),
    }


def cmd_cancel(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    lock_path = root / ".session.json"
    lock = read_json(lock_path)
    lock_path.unlink()
    return {"status": "cancelled", "session_id": lock.get("session_id")}


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(description=__doc__)
    sub = top.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize a local course directory")
    init.add_argument("--root", required=True)
    init.add_argument("--course-pack", required=True)
    init.add_argument("--goal")
    init.add_argument("--minutes", type=int, default=30)
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    begin = sub.add_parser("begin", help="Open one session and print its brief")
    begin.add_argument("--root", required=True)
    begin.add_argument("--minutes", type=int, default=30)
    begin.set_defaults(func=cmd_begin)

    close = sub.add_parser("close", help="Validate evidence and atomically close a session")
    close.add_argument("--root", required=True)
    close.add_argument("--evidence", required=True)
    close.set_defaults(func=cmd_close)

    status = sub.add_parser("status", help="Summarize progress and due reviews")
    status.add_argument("--root", required=True)
    status.set_defaults(func=cmd_status)

    cancel = sub.add_parser("cancel", help="Cancel an open session without progress")
    cancel.add_argument("--root", required=True)
    cancel.set_defaults(func=cmd_cancel)
    return top


def main() -> int:
    args = parser().parse_args()
    try:
        result = args.func(args)
    except TutorStateError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
