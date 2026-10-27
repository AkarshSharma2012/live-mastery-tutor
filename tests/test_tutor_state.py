import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "skills" / "live-mastery-tutor" / "scripts" / "tutor_state.py"


class TutorStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "course"
        self.pack = Path(self.temp.name) / "pack.json"
        self.pack.write_text(
            json.dumps(
                {
                    "id": "test-course",
                    "title": "Test Course",
                    "mastery_threshold": 0.8,
                    "sources": [],
                    "domains": [
                        {
                            "id": "D1",
                            "title": "Domain",
                            "weight": "100%",
                            "objectives": [
                                {
                                    "id": "D1.1",
                                    "outcome": "Perform the task",
                                    "hands_on": True,
                                    "confusable_with": [],
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.cli("init", "--root", str(self.root), "--course-pack", str(self.pack))

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, *args, expect=0):
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, expect, msg=result.stderr)
        stream = result.stdout if expect == 0 else result.stderr
        return json.loads(stream)

    def begin(self):
        return self.cli("begin", "--root", str(self.root), "--minutes", "20")

    def close(self, session_id, events):
        evidence = Path(self.temp.name) / f"{session_id}.json"
        evidence.write_text(
            json.dumps({"session_id": session_id, "events": events}),
            encoding="utf-8",
        )
        return self.cli("close", "--root", str(self.root), "--evidence", str(evidence))

    def test_mastery_requires_immediate_gates_and_two_later_reviews(self):
        session = self.begin()
        base = {"topic_id": "D1.1", "result": "independent_correct", "observed": "verified"}
        events = [
            {**base, "kind": "instruction", "result": "observed"},
            {**base, "kind": "teach_back"},
            {**base, "kind": "hands_on"},
            {**base, "kind": "contrast"},
            {**base, "kind": "quiz", "score": 0.8},
        ]
        self.close(session["session_id"], events)
        state = json.loads((self.root / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["topics"]["D1.1"]["status"], "reviewing")

        for expected in (1, 2):
            session = self.begin()
            self.close(session["session_id"], [{**base, "kind": "review"}])
            state = json.loads((self.root / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["topics"]["D1.1"]["review_successes"], expected)

        self.assertEqual(state["topics"]["D1.1"]["status"], "mastered")

    def test_prompted_review_does_not_advance(self):
        session = self.begin()
        self.close(
            session["session_id"],
            [
                {
                    "topic_id": "D1.1",
                    "kind": "review",
                    "result": "prompted_correct",
                    "prompted": True,
                    "observed": "correct after a hint",
                }
            ],
        )
        state = json.loads((self.root / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["topics"]["D1.1"]["review_successes"], 0)

    def test_mismatched_session_is_rejected_without_state_change(self):
        session = self.begin()
        evidence = Path(self.temp.name) / "bad.json"
        evidence.write_text(
            json.dumps(
                {
                    "session_id": "wrong",
                    "events": [
                        {
                            "topic_id": "D1.1",
                            "kind": "instruction",
                            "result": "observed",
                            "observed": "lesson",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.cli("close", "--root", str(self.root), "--evidence", str(evidence), expect=2)
        self.assertTrue((self.root / ".session.json").exists())
        state = json.loads((self.root / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["session_count"], 0)
        self.assertEqual(session["session_id"], json.loads((self.root / ".session.json").read_text())["session_id"])


if __name__ == "__main__":
    unittest.main()
