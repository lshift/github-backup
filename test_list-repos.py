from .list_repos import runLists

from .testFramework import TestCase

class TestListRepos(TestCase):
    def test_basic(self):
        config = {
            "logging": "DEBUG",
            "admin-token": self.test_admin_token,
            "org": self.test_org,
            "default-access": "pull"
        }
        runLists(config)

if __name__ == '__main__':
    unittest.main()
