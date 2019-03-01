import unittest
from ..compare_permissions import gen_changes

class TestComparePermissions(unittest.TestCase):
    def test_list_ordering(self):
        access = {"access": [
            {"what": "admin", "who": "foo", "why": '[Owner]'},
            {"what": "admin", "who": "bar", "why": '[Owner]'}
            ]}
        res = gen_changes({"repo2": access, "repo1": access}, [])
        assert res == [
            'bar has been added to repo1 with permissions admin because of [Owner]',
            'bar has been added to repo2 with permissions admin because of [Owner]',
            'foo has been added to repo1 with permissions admin because of [Owner]',
            'foo has been added to repo2 with permissions admin because of [Owner]'
        ]