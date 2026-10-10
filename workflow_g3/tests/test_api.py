import os
import tempfile
import unittest

try:
    from fastapi.testclient import TestClient
    from workflow.api import create_app
    HAVE_FASTAPI = True
except ImportError:
    HAVE_FASTAPI = False

from workflow.db import connect, init_db
from workflow.seed import seed_base

P = "/api/v1"

@unittest.skipUnless(HAVE_FASTAPI, "fastapi/httpx no instalados")
class ApiTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = connect(self.path)
        init_db(conn)
        self.ids = seed_base(conn)
        conn.close()
        self.client = TestClient(create_app(self.path))

    def tearDown(self):
        os.remove(self.path)

    def h(self, uid):
        return {"X-User-Id": str(uid)}

    def new_task_with_recipients(self, rule=None):
        c, coord = self.client, self.h(self.ids["coord"])
        t = c.post(f"{P}/tasks", headers=coord, json={
            "type_id": self.ids["types"]["update_program"], "title": "Programa",
            "due_date": "2026-10-30", "reviewer_id": self.ids["reviewer"]})
        self.assertEqual(t.status_code, 201)
        tid = t.json()["id"]
        r = c.post(f"{P}/tasks/{tid}/recipients", headers=coord, json=rule or {"mode": "all"})
        self.assertEqual(r.status_code, 200)
        return tid

    def test_full_cycle_and_error_codes(self):
        c, coord = self.client, self.h(self.ids["coord"])
        tid = self.new_task_with_recipients()
        pub = c.post(f"{P}/tasks/{tid}/publish", headers=coord)
        self.assertEqual(pub.status_code, 200)
        self.assertEqual(pub.json()["assignments_created"], 5)
        self.assertEqual(c.post(f"{P}/tasks/{tid}/publish", headers=coord).status_code, 409)

        t0 = self.ids["teachers"][0]
        aid = pub.json()["assignment_ids"][0]
        act = lambda a, uid, body=None: c.post(f"{P}/assignments/{aid}/actions/{a}",
                                               headers=self.h(uid), json=body or {})
        self.assertEqual(act("start", self.ids["teachers"][1]).status_code, 403)
        self.assertEqual(act("approve", t0).status_code, 403)
        self.assertEqual(act("submit", t0).status_code, 409)
        self.assertEqual(act("start", t0).json()["status"], "in_progress")
        act("submit", t0)
        act("review", self.ids["reviewer"])
        self.assertEqual(act("return", self.ids["reviewer"]).status_code, 422)
        self.assertEqual(act("return", self.ids["reviewer"], {"comment": "Corrija"}).status_code, 200)

        hist = c.get(f"{P}/assignments/{aid}/history", headers=coord).json()["items"]
        self.assertEqual(hist[-1]["to_status"], "returned")
        summary = c.get(f"{P}/tasks/{tid}/assignments", headers=coord).json()["summary"]
        self.assertEqual(summary["by_status"]["returned"], 1)
        self.assertEqual(c.get(f"{P}/events", headers=self.h(self.ids["authority"])).status_code, 200)

    def test_draft_not_in_inbox_and_error_format(self):
        c = self.client
        self.new_task_with_recipients()                       # sigue en borrador
        inbox = c.get(f"{P}/assignments/inbox", headers=self.h(self.ids["teachers"][0]))
        self.assertEqual(inbox.json()["total"], 0)
        self.assertEqual(c.get(f"{P}/tasks").status_code, 401)
        bad = c.post(f"{P}/tasks", headers=self.h(self.ids["coord"]), json={"title": "x"})
        self.assertEqual(bad.status_code, 422)
        self.assertIn("error", bad.json())


if __name__ == "__main__":
    unittest.main()
