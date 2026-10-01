import json
import tempfile
import unittest
from pathlib import Path

from settings import ConfigurationError, Settings, load_settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "config.json"

    def write_config(self, data):
        self.path.write_text(json.dumps(data))

    def test_token_only_environment_needs_no_database(self):
        settings = load_settings(self.path, {"BOT_TOKEN": "test-token"})
        self.assertIsNone(settings.mongo_uri)
        self.assertEqual(settings.extensions, ("Utils.member_setup",))

    def test_local_config_fallback(self):
        self.write_config({"token": "local-token", "db_connection": "mongodb://local"})
        settings = load_settings(self.path, {})
        self.assertEqual(settings.token, "local-token")
        self.assertEqual(settings.mongo_uri, "mongodb://local")

    def test_environment_overrides_local_credentials(self):
        self.write_config({"token": "local-token", "db_connection": "mongodb://local"})
        settings = load_settings(
            self.path, {"BOT_TOKEN": "env-token", "MONGO_ACCESS": "mongodb://env"}
        )
        self.assertEqual(settings.token, "env-token")
        self.assertEqual(settings.mongo_uri, "mongodb://env")

    def test_mixed_environment_and_config(self):
        self.write_config({"db_connection": "mongodb://local"})
        settings = load_settings(self.path, {"BOT_TOKEN": "env-token"})
        self.assertEqual(settings.mongo_uri, "mongodb://local")

    def test_missing_token_has_actionable_error(self):
        with self.assertRaisesRegex(ConfigurationError, "BOT_TOKEN"):
            load_settings(self.path, {})

    def test_invalid_config_does_not_expose_contents(self):
        self.path.write_text("secret-invalid-json")
        with self.assertRaises(ConfigurationError) as raised:
            load_settings(self.path, {})
        self.assertNotIn("secret", str(raised.exception))

    def test_invalid_credential_types(self):
        for data in ({"token": 1}, {"token": "test", "db_connection": []}, []):
            with self.subTest(data=data):
                self.write_config(data)
                with self.assertRaises(ConfigurationError):
                    load_settings(self.path, {})

    def test_settings_repr_hides_credentials(self):
        settings = Settings(token="secret-token", mongo_uri="secret-uri")
        self.assertNotIn("secret", repr(settings))
