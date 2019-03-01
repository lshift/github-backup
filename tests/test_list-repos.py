from ..list_repos import runLists, load_config
from .testFramework import TestCase
import unittest

class TestListRepos(TestCase):
    def test_basic(self):
        config = {
            "logging": "DEBUG",
            "admin-token": self.test_admin_token,
            "org": self.test_org,
            "default-access": "pull"
        }
        runLists(config)

    def test_config_load(self):
        config = load_config("tests/example.yaml")
        assert config["backup_folder"] == "foo"
        assert config["repos"] == "bar"

if __name__ == '__main__':
    unittest.main()
