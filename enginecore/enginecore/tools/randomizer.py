"""Aggregate functionalities related to randomizing actions"""
import random
import functools
import inspect
import time
import sys
import types


class Randomizer:
    """Randomizer is a chaos generator that can perform random actions
    associated with a class/or its instance
    """

    # contains all the classes registered with Randomizer.register
    classes = {}

    # seed used for predictable randomization
    seed = None

    @classmethod
    def _rand_action(cls, rand_obj, nap):
        """Perform rand action associated with the passed object"""
        rand_func = random.choice(cls.classes[rand_obj.__class__])
        rand_args = list(map(lambda x: x(), rand_func.arg_defaults))

        full_func_args = inspect.getfullargspec(rand_func.__wrapped__).args

        if "self" in full_func_args or "cls" in full_func_args:
            rand_func(rand_obj, *tuple(rand_args))
        else:
            rand_func(*tuple(rand_args))

        # majestic nap
        if nap:
            nap()

    @classmethod
    def set_seed(cls, seed=random.randrange(sys.maxsize)):
        """Update randomizer seed"""
        random.seed(seed)
        # store in Randomizer since there's no seed getter in random
        cls.seed = seed

    @classmethod
    def get_seed(cls):
        """get randomizer seed"""
        return cls.seed

    @classmethod
    def randact(
        cls, instance, num_iter: int = 1, seconds: int = None, nap: callable = None
    ):
        """Perform random action on an object"""

        if seconds and seconds < 0:
            raise ValueError("Argument 'seconds' must be postivie")

        # received multiple objects
        if isinstance(instance, list):
            obj_classes = map(lambda x: x.__class__, instance)

            # Classes not registered in cls.classes
            if set(obj_classes).difference(set(cls.classes)) != set():
                raise ValueError("Unsupported/unregistered classes detected")
        elif instance.__class__ not in cls.classes:
            raise ValueError(
                "Unregistered class '{}'".format(instance.__class__.__name__)
            )

        if not isinstance(instance, list):
            instance = [instance]

        rand_obj = lambda: random.choice(instance)
        # either perform rand actions for 'n' seconds or for 'n' iterations
        if seconds:
            t_end = time.time() + seconds
            if not nap:
                nap = functools.partial(time.sleep, 1)

            while time.time() < t_end:
                cls._rand_action(rand_obj(), nap)
        else:
            list(map(lambda _: cls._rand_action(rand_obj(), nap), range(num_iter)))

    @classmethod
    def register(cls, new_reg_cls):
        """Register class as randomizable with @Randomizer.register decorator
        Randomizer will search for recordable methods & store them as randomly-replayable
        """
        cls_details = []

        # Find methods/classmethods with @Recorder()
        # decorator attached to them
        for attr_name in dir(new_reg_cls):
            attr = getattr(new_reg_cls, attr_name)

            # see https://stackoverflow.com/a/41696531
            if isinstance(attr, types.MethodType):
                attr = attr.__func__

            if hasattr(attr, "recordable") and attr.recordable:
                cls_details.append(attr)

        cls.classes[new_reg_cls] = cls_details
        return new_reg_cls


Randomizer.set_seed()
