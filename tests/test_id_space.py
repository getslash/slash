from .utils import TestCase
from slash import Session

class TestIDSpace(TestCase):
    def test_ids_are_unique(self):
        ids = []
        for _ in range(2):
            with Session() as session:
                ids.append(session.id)
                ids.append(session.id_space.allocate())
        self.assertEqual(len(ids), len(set(ids)), "IDs are not unique")
