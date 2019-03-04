from ..list_repos import runLists, load_config, max_permission
from .testFramework import TestCase
import unittest

class TestListRepos(TestCase):
    def test_basic(self):
        config = {
            "logging": "DEBUG",
            "admin-token": self.test_admin_token,
            "org": self.test_org,
        }
        runLists(config)

    def test_config_load(self):
        config = load_config("tests/example.yaml")
        assert config["backup_folder"] == "foo"
        assert config["repos"] == "bar"

    def test_parse_none(self):
        assert max_permission(["none"]) == "none"
        assert max_permission(["admin", "none"]) == "admin"

if __name__ == '__main__':
    unittest.main()
