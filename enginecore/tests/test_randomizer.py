"""Unittests for testing action randomizer (chaos engine) """

import unittest
import random
import time

from datetime import datetime as dt

from enginecore.tools.recorder import Recorder
from enginecore.tools.randomizer import Randomizer


REC = Recorder(module=__name__)


def _get_b(_):
    """return random b value from a range"""
    return random.choice(["b", "bb", "bb"])


def _get_obj(_):
    """return random object"""
    return random.choice([dt.now(), {"message": "!"}, RandomizedEntity()])


class Dummy:
    """Unregistered class"""

    pass


@Randomizer.register
class RandomizedEntity:
    """Actions/methods callas of the instance of this class will be randomly generated"""

    num_entities = 0
    cls_lvl_number = 0

    def __init__(self):
        self.count = 0
        self.a_str = "a"
        self.b_str = "b"
        self.obj = dt.now()

        RandomizedEntity.num_entities = RandomizedEntity.num_entities + 1
        self.key = RandomizedEntity.num_entities

    @REC
    @Randomizer.randomize_method((lambda _: random.randrange(0, 10),))
    def set_count(self, value):
        """Test method 1"""
        self.count = value

    @REC
    @Randomizer.randomize_method((lambda _: random.choice(["a", "aa", "aaa"]), _get_b))
    def set_kwargs(self, a_str="a", b_str="b"):
        """Test method 2"""
        self.a_str = a_str
        self.b_str = b_str

    @REC
    @Randomizer.randomize_method((_get_obj,))
    def set_object(self, obj):
        """Test method 3"""
        self.obj = obj

    @REC
    @Randomizer.randomize_method()
    def no_args(self):
        """Test method 4"""
        pass

    def not_safe_for_recording(self):
        """Test method excluded from recording/randomization"""
        pass

    @classmethod
    @REC
    @Randomizer.randomize_method()
    def class_method_1(cls):
        """Test class method 1"""
        pass

    @classmethod
    @REC
    @Randomizer.randomize_method((lambda _: random.randrange(0, 1),))
    def class_method_2(cls, number):
        """Test class method 2"""
        cls.cls_lvl_number = number

    # @staticmethod
    # @Randomizer.randomize_method((lambda _: random.randrange(0, 1),))
    # def static_method_1(number):
    #     """Test static method"""
    #     RandomizedEntity.cls_lvl_number = number


@Randomizer.register
class RandomizedEntityParent:
    def __init__(self):
        self.key = 0

    @REC
    @Randomizer.randomize_method((lambda _: random.randrange(0, 10),))
    def test_method(self, value):
        """Test method 4"""
        time.time()


@Randomizer.register
class RandomizedEntity2:
    def __init__(self):
        self.status = 0
        self.key = 0

    @REC
    @Randomizer.randomize_method((lambda self: 1 if self.status < 1 else 0,))
    def determine_status_from_self(self, value):
        """Test method 5"""
        self.status = value


@Randomizer.register
class RandomizedEntityChild(RandomizedEntityParent):
    @Randomizer.randomize_method((lambda _: random.randrange(0, 10),))
    def test_method(self, value):
        """Test method 4"""
        time.time()
        super().test_method(value)


@Randomizer.register
class Employee:
    """Yet another randomized entity (a bit more meaningful this time)"""

    employee_num = 0
    num_promotions = 0

    def __init__(self):
        self.title = "developer"
        Employee.employee_num = Employee.employee_num + 1
        self.key = Employee.employee_num

    @REC
    @Randomizer.randomize_method(
        (lambda _: random.choice(["manager", "ceo", "cto", "janitor"]),)
    )
    def assign_title(self, title):
        """Test method 1"""
        Employee.num_promotions = Employee.num_promotions + 1
        self.title = title


class RandomizerTests(unittest.TestCase):
    """Test action randomizer"""

    def setUp(self):
        self.rand_entity_1 = RandomizedEntity()
        self.rand_child_entity_1 = RandomizedEntityChild()
        self.employee = Employee()
        # Randomizer.set_seed(1)

    def tearDown(self):
        # clean-up
        REC.enabled = True
        REC.erase_all()
        RandomizedEntity.num_entities = 0
        RandomizedEntity.cls_lvl_number = 0
        Employee.employee_num = 0
        Employee.num_promotions = 0
        # Randomizer.set_seed(1)

    def test_registered_classes(self):
        """Test that randomized classes are registered in Randomizer"""
        self.assertIn(RandomizedEntity, Randomizer.classes)
        self.assertIn(Employee, Randomizer.classes)

    def test_registered_methods(self):
        """Test randomized methods are registered by the Randomizer"""

        rand_entity_recorded_methods = [
            RandomizedEntity.set_count,
            RandomizedEntity.set_kwargs,
            RandomizedEntity.set_object,
            RandomizedEntity.no_args,
            RandomizedEntity.class_method_1,
            RandomizedEntity.class_method_2,
            # RandomizedEntity.static_method_1,
        ]

        self.assertEqual(
            len(rand_entity_recorded_methods), len(Randomizer.classes[RandomizedEntity])
        )

        self.assertIn(Employee.assign_title, Randomizer.classes[Employee])

    def test_excluded_method(self):
        """Verify that methods not marked with a decorator do not get randomized"""
        self.assertNotIn(
            RandomizedEntity.not_safe_for_recording,
            Randomizer.classes[RandomizedEntity],
        )

    def test_unregistered_class(self):
        """Test invalid instance"""
        unreg_obj = Dummy()

        with self.assertRaises(ValueError):
            Randomizer.randact(unreg_obj)

    def test_randact(self):
        """Verify randact performing one random action"""
        Randomizer.randact(self.employee, num_iter=1)
        self.assertEqual(1, Employee.num_promotions)
        self.assertIn(self.employee.title, ["manager", "ceo", "cto", "janitor"])

    def test_randact_iter(self):
        """Test randomizer performing specified number of actions"""
        Randomizer.randact(self.employee, num_iter=20, nap=lambda: None)
        self.assertEqual(20, Employee.num_promotions)

    def test_randact_timed(self):
        """Verify time based action execution"""
        Randomizer.randact(self.employee, seconds=4, nap=lambda: time.sleep(1))
        self.assertGreater(Employee.num_promotions, 1)

    def test_randact_many_invalid(self):
        """Verify illegal class instance raising exception"""
        unreg_obj = Dummy()

        with self.assertRaises(ValueError):
            Randomizer.randact([self.employee, self.rand_entity_1, unreg_obj])

    def test_randact_many(self):
        """Verify randomized actions with various instances"""
        Randomizer.randact(
            [self.employee, self.rand_entity_1], num_iter=20, nap=lambda: None
        )
        recorder_history = REC.get_action_details()
        self.assertEqual(20, len(recorder_history))

    def test_recorder(self):
        """Test action randomizer"""
        self.assertEqual(0, len(REC.get_action_details()))
        Randomizer.randact(self.employee)
        self.assertEqual(1, len(REC.get_action_details()))
        Randomizer.randact(
            [self.employee, self.rand_entity_1], num_iter=9, nap=lambda: None
        )
        self.assertEqual(10, len(REC.get_action_details()))

    def test_child_class(self):
        """Verify that inherited methods get randomized as well"""
        Randomizer.randact(self.rand_child_entity_1)
        self.assertEqual(1, len(REC.get_action_details()))
        self.assertTrue(
            REC.get_action_details()[0]["work"].startswith(
                "RandomizedEntityChild(0).test_method"
            )
        )

    def test_arg_from_object(self):
        """Test that you can access object when randomizing function argument"""
        test_entity_2 = RandomizedEntity2()
        Randomizer.randact(test_entity_2)
        self.assertEqual(1, test_entity_2.status)
        test_entity_2.status = 0

        Randomizer.randact(test_entity_2, num_iter=5, nap=lambda: None)
        self.assertEqual(1, test_entity_2.status)


if __name__ == "__main__":
    unittest.main()
