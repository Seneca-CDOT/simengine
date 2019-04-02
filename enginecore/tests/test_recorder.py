"""Unittests for testing action recorder & action history replay"""

import unittest

from enginecore.tools.recorder import Recorder
from enginecore.model.graph_reference import GraphReference


REC = Recorder(module=__name__)


class RecordedEntity:
    """Class to be "recorded" """

    num_entities = 0
    test_a = {"value": 2}

    def __init__(self, key=None):
        self.count = 0
        self._graph_ref = GraphReference()

        RecordedEntity.num_entities = RecordedEntity.num_entities + 1
        self.key = RecordedEntity.num_entities if not key else key

    @REC
    def add(self, value):
        """Test method 1"""
        self.count = self.count + value

    @REC
    def subtract(self, value):
        """Test method 2"""
        self.count = self.count - value

    @REC
    def double_a(self):
        """Test method 3"""
        RecordedEntity.test_a["value"] = RecordedEntity.test_a["value"] * 2

    @classmethod
    @REC
    def class_lvl_method(cls):
        """Test class method"""
        pass


class RecorderTests(unittest.TestCase):
    """Tests for action Recorder class"""

    def setUp(self):
        self.recorded_entity_1 = RecordedEntity()
        self.recorded_entity_2 = RecordedEntity()

    def tearDown(self):
        # clean-up
        REC.enabled = True
        REC.erase_all()
        RecordedEntity.num_entities = 0
        RecordedEntity.test_a = {"value": 2}

    def test_record(self):
        """Test if action is getting stored"""
        self.recorded_entity_1.add(3)
        self.recorded_entity_2.add(2)

        self.recorded_entity_1.subtract(2)
        RecordedEntity.class_lvl_method()

        action_details = REC.get_action_details()

        self.assertEqual(4, len(action_details))
        expected_work_str = [
            "RecordedEntity(1).add(3,)",
            "RecordedEntity(2).add(2,)",
            "RecordedEntity(1).subtract(2,)",
            "RecordedEntity.class_lvl_method()",
        ]

        for idx, action in enumerate(action_details):
            self.assertEqual(expected_work_str[idx], action["work"])

    def test_replay_all(self):
        """Test that actions can be replayed"""

        self.recorded_entity_1.add(1)
        self.recorded_entity_1.add(1)
        self.recorded_entity_1.add(1)
        self.recorded_entity_1.subtract(1)

        self.assertEqual(2, self.recorded_entity_1.count)

        REC.replay_all()
        self.assertEqual(4, self.recorded_entity_1.count)

        REC.replay_all()
        REC.replay_all()
        self.assertEqual(8, self.recorded_entity_1.count)

    def test_replay_range(self):
        """Replay only a range of actions"""

        self.recorded_entity_1.add(1)
        self.recorded_entity_1.add(1)
        self.recorded_entity_1.add(1)

        self.recorded_entity_1.subtract(3)
        self.assertEqual(0, self.recorded_entity_1.count)

        # perform only add
        REC.replay_range(slice(0, 3))
        self.assertEqual(3, self.recorded_entity_1.count)

        # only subtract (last op)
        REC.replay_range(slice(-1, None))
        self.assertEqual(0, self.recorded_entity_1.count)

    def test_erase_all(self):
        """Test that action can be deleted"""
        self.recorded_entity_1.add(5)
        self.recorded_entity_2.add(5)

        self.assertEqual(5, self.recorded_entity_1.count)
        self.assertEqual(5, self.recorded_entity_2.count)

        REC.erase_all()
        REC.replay_all()
        self.assertEqual(5, self.recorded_entity_1.count)
        self.assertEqual(5, self.recorded_entity_2.count)

    def test_erase_range(self):
        """Test that a range of actions can be removed"""
        self.recorded_entity_1.add(1)
        self.recorded_entity_1.add(1)
        self.recorded_entity_1.add(1)

        self.assertEqual(3, self.recorded_entity_1.count)
        REC.erase_range(slice(1, 2))
        REC.replay_all()
        self.assertEqual(5, self.recorded_entity_1.count)

    def test_enabled(self):
        """Test that recorder can be disabled & stop recording"""

        self.recorded_entity_1.add(1)
        self.recorded_entity_1.add(1)

        REC.enabled = False
        self.recorded_entity_1.add(1)
        self.recorded_entity_1.add(1)

        REC.replay_all()

        # 2 + 2 original actions plus 2 replayed actions
        self.assertEqual(6, self.recorded_entity_1.count)

    def test_serialization(self):
        """Test action saving functionality"""

        self.recorded_entity_1.double_a()  # 4
        self.recorded_entity_2.double_a()  # 8

        self.recorded_entity_1.add(1)
        RecordedEntity.class_lvl_method()

        REC.save_actions(action_file="/tmp/simengine_rec_utest.json")
        self.recorded_entity_1.double_a()  # 16 (action not saved)
        self.assertEqual(16, RecordedEntity.test_a["value"])
        # Action history: a * 2 * 2 where test_a = 16

        new_recorder = Recorder(module=__name__)
        new_recorder.load_actions(
            map_key_to_state=RecordedEntity, action_file="/tmp/simengine_rec_utest.json"
        )

        new_recorder.replay_all()

        self.assertEqual(64, RecordedEntity.test_a["value"])

        action_details = new_recorder.get_action_details()
        self.assertEqual(4, len(action_details))

    def test_serialization_save_range(self):
        """Test action saving but only slice of action history"""
        self.recorded_entity_1.double_a()  # 4
        self.recorded_entity_1.double_a()  # 8
        self.recorded_entity_1.double_a()  # 16

        # serialize only the last action
        REC.save_actions(
            action_file="/tmp/simengine_rec_utest.json", slc=slice(-1, None)
        )

        new_recorder = Recorder(module=__name__)
        new_recorder.load_actions(
            map_key_to_state=RecordedEntity, action_file="/tmp/simengine_rec_utest.json"
        )

        new_recorder.replay_all()
        self.assertEqual(32, RecordedEntity.test_a["value"])
        action_details = new_recorder.get_action_details()
        self.assertEqual(1, len(action_details))

    def test_serialization_load_range(self):
        """Test action loading but only slice of action history"""

        self.recorded_entity_1.double_a()  # 4
        self.recorded_entity_1.double_a()  # 8
        self.recorded_entity_1.double_a()  # 16

        # serialize only the last action
        REC.save_actions(action_file="/tmp/simengine_rec_utest.json")

        new_recorder = Recorder(module=__name__)
        new_recorder.load_actions(
            map_key_to_state=RecordedEntity,
            action_file="/tmp/simengine_rec_utest.json",
            slc=slice(-1, None),
        )

        new_recorder.replay_all()
        self.assertEqual(32, RecordedEntity.test_a["value"])
        action_details = new_recorder.get_action_details()
        self.assertEqual(1, len(action_details))


if __name__ == "__main__":
    unittest.main()
