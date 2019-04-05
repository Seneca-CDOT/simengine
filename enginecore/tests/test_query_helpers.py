"""Unittests for various database helpers"""
import unittest
import enginecore.tools.query_helpers as qh


class QueryHelperTests(unittest.TestCase):
    """Tests some query helper functionalities"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_props_stm(self):
        """Test props statement used to init node attributes"""
        attr = {"a": 1, "b": 2, "c": 3}
        formatted_stm = qh.get_props_stm(attr)
        self.assertEqual("a: 1,b: 2,c: 3", formatted_stm)

    def test_get_props_stm_filter(self):
        """Test if supported attr filters out attr"""
        attr = {"a": 1, "b": 2, "c": 3, "d": 4}
        s_attr = ["a", "b", "c"]
        formatted_stm = qh.get_props_stm(attr, supported_attr=s_attr)
        self.assertEqual("a: 1,b: 2,c: 3", formatted_stm)

    def test_set_stm(self):
        """Test statement formatter used for updating node attributes"""
        attr = {"a": 1, "b": 2, "c": 3}
        formatted_stm = qh.get_set_stm(attr, node_name="test")
        self.assertEqual("test.a=1,test.b=2,test.c=3", formatted_stm)

    def test_set_stm_filter(self):
        """Test if supported attr filters out attr"""
        attr = {"a": 1, "b": 2, "c": 3, "d": 4}
        s_attr = ["a", "b", "c"]
        formatted_stm = qh.get_set_stm(attr, node_name="test", supported_attr=s_attr)
        self.assertEqual("test.a=1,test.b=2,test.c=3", formatted_stm)

    def test_oid_desc_stm(self):
        """Test if OIDs description get formatted correctly"""
        init_desc = {"1": "desc1", "2": "desc2", "3": "desc3"}
        oid_desc = dict((y, x) for x, y in init_desc.items())

        formatted_stm = qh.get_oid_desc_stm(oid_desc)
        self.assertEqual('`1`: "desc1",`2`: "desc2",`3`: "desc3"', formatted_stm)


if __name__ == "__main__":
    unittest.main()
