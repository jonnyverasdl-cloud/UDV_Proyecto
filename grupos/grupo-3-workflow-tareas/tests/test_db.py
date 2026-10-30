"""Pruebas de la capa de base de datos sin necesitar un MySQL real (conexión simulada)."""
import os
import unittest
from unittest.mock import patch

from workflow import db
from workflow.db import MySQLConn, Row, connect, get_database_url, set_actor, transaction


class FakeCursor:
    def __init__(self, log):
        self.log, self.description, self.lastrowid, self.rowcount = log, [("id",), ("name",)], 7, 1

    def execute(self, sql, params=None):
        self.log.append((sql, params))

    def fetchone(self):
        return (1, "Ana")

    def fetchall(self):
        return [(1, "Ana"), (2, "Luis")]


class FakeRaw:
    def __init__(self):
        self.log, self.commits, self.rollbacks = [], 0, 0

    def cursor(self):
        return FakeCursor(self.log)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class MySQLAdapterTests(unittest.TestCase):
    def setUp(self):
        self.raw = FakeRaw()
        self.conn = MySQLConn(self.raw)

    def test_placeholders_are_translated(self):
        self.conn.execute("SELECT * FROM users WHERE id = ? AND active = ?", (3, 1))
        self.assertEqual(self.raw.log[-1], ("SELECT * FROM users WHERE id = %s AND active = %s", (3, 1)))

    def test_rows_work_like_sqlite_rows(self):
        row = self.conn.execute("SELECT id, name FROM users").fetchone()
        self.assertEqual((row["id"], row["name"], row[0], row[1]), (1, "Ana", 1, "Ana"))
        self.assertEqual(dict(row), {"id": 1, "name": "Ana"})
        self.assertEqual(tuple(row), (1, "Ana"))
        self.assertEqual([dict(r)["name"] for r in self.conn.execute("SELECT 1")], ["Ana", "Luis"])

    def test_set_actor_runs_set_actor_id(self):
        set_actor(self.conn, 42)
        self.assertEqual(self.raw.log[-1], ("SET @actor_id = %s", (42,)))

    def test_set_actor_is_noop_on_sqlite(self):
        set_actor(connect(":memory:"), 42)          # no debe fallar

    def test_transaction_commits_and_rolls_back(self):
        with transaction(self.conn):
            self.assertTrue(self.conn.in_transaction)
            with transaction(self.conn):             # anidada: participa en la misma
                pass
        self.assertEqual((self.raw.commits, self.raw.rollbacks), (1, 0))
        self.assertFalse(self.conn.in_transaction)
        with self.assertRaises(ValueError):
            with transaction(self.conn):
                raise ValueError("falla")
        self.assertEqual((self.raw.commits, self.raw.rollbacks), (1, 1))

    def test_init_db_refuses_mysql(self):
        with self.assertRaises(RuntimeError):
            db.init_db(self.conn)


class DatabaseUrlTests(unittest.TestCase):
    def test_reads_database_url_from_env(self):
        with patch.dict(os.environ, {"DATABASE_URL": "mysql+pymysql://u:p@h:3306/x"}):
            self.assertEqual(get_database_url(), "mysql+pymysql://u:p@h:3306/x")

    def test_sqlite_url_and_plain_path(self):
        a = connect("sqlite:///:memory:")
        b = connect(":memory:")
        for conn in (a, b):
            conn.execute("CREATE TABLE t (id INTEGER)")
            conn.close()


if __name__ == "__main__":
    unittest.main()
