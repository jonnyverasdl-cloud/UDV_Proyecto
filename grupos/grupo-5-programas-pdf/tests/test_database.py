from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from g5_programas.auth import Actor
from g5_programas.database import get_session, set_database_actor


class DatabaseSessionTests(unittest.TestCase):
    """Comprueba la selección y el cierre de la sesión por solicitud."""

    def test_uses_host_factory_when_configured(self):
        session = Mock()
        session.info = {}
        factory = Mock(return_value=session)
        request = SimpleNamespace(
            client=None,
            app=SimpleNamespace(
                state=SimpleNamespace(database_session_factory=factory)
            )
        )

        self.assertEqual(next(get_session(request)), session)

        factory.assert_called_once_with()
        session.close.assert_called_once_with()

    def test_uses_database_url_factory_when_host_factory_is_missing(self):
        session = Mock()
        session.info = {}
        fallback_factory = Mock(return_value=session)
        request = SimpleNamespace(client=None, app=SimpleNamespace(state=SimpleNamespace()))

        with patch("g5_programas.database._session_factory", return_value=fallback_factory) as fallback:
            self.assertEqual(next(get_session(request)), session)

        fallback.assert_called_once_with()
        fallback_factory.assert_called_once_with()
        session.close.assert_called_once_with()

    def test_sets_database_actor_through_g2_helper_with_request_ip(self):
        session = Mock()
        session.info = {"ip_origen": "192.0.2.10"}
        actor = Actor(id=12, name="Docente", roles=frozenset({"teacher"}))

        with patch("g5_programas.database.fijar_actor") as g2_helper:
            set_database_actor(session, actor)

        g2_helper.assert_called_once_with(session, 12, "192.0.2.10")

    def test_sets_actor_and_ip_directly_when_g2_is_unavailable(self):
        session = Mock()
        session.info = {"ip_origen": "192.0.2.10"}
        actor = Actor(id=12, name="Docente", roles=frozenset({"teacher"}))

        with patch("g5_programas.database.fijar_actor", None):
            set_database_actor(session, actor)

        statement, parameters = session.execute.call_args.args
        self.assertIn("@actor_id = :actor_id", str(statement))
        self.assertIn("@ip_origen = :ip_origen", str(statement))
        self.assertEqual(parameters, {"actor_id": 12, "ip_origen": "192.0.2.10"})


if __name__ == "__main__":
    unittest.main()
