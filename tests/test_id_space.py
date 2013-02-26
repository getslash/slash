from .utils import TestCase
from shakedown.session import Session
from shakedown.suite import Suite

class TestIDSpace(TestCase):
    def test_ids_are_unique(self):
        ids = []
        for _ in range(2):
            with Session() as session:
                ids.append(session.id)
                with Suite() as suite:
                    ids.append(suite.id)
                    ids.append(suite.id_space.allocate())
        self.assertEquals(len(ids), len(set(ids)), "IDs are not unique")
