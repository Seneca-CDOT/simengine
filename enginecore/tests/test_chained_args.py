"""Unittests for testing chained arguments"""

import unittest
from enginecore.tools.randomizer import ChainedArgs


class Add3:
    """Adds 3 numbers"""

    def __init__(self):
        self.scalar = 10

    def abc(self, _1st, _2nd, _3rd):
        """funct with args to be tested"""
        return _1st + _2nd + _3rd


class ChainedArgsTests(unittest.TestCase):
    """Test chained arguments"""

    def setUp(self):
        self.add3 = Add3()
        self.calc_args = lambda obj, args: map(lambda x: x(obj), args)

    def test_simple_args(self):
        """Test that chained args can be passed"""

        chained = ChainedArgs([lambda self: 1, lambda self, _: 1, lambda self, _: 1])()
        result = self.add3.abc(*self.calc_args(self.add3, chained))
        self.assertEqual(3, result)

    def test_self_in_args(self):
        """Objec itself is accessible when calculating arguments"""

        chained = ChainedArgs(
            [
                lambda self: 1 * self.scalar,
                lambda self, _: 1 * self.scalar,
                lambda self, _: 1 * self.scalar,
            ]
        )()
        result = self.add3.abc(*self.calc_args(self.add3, chained))
        self.assertEqual(30, result)

    def test_chained_args(self):
        """Next arguments have access to previously calculated values"""

        chained = ChainedArgs(
            [lambda self: 1, lambda self, prev: 1 + prev, lambda self, prev: 1 + prev]
        )()
        result = self.add3.abc(*self.calc_args(self.add3, chained))
        self.assertEqual(6, result)


if __name__ == "__main__":
    unittest.main()
