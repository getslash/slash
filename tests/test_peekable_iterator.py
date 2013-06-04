from .utils import TestCase
from slash.utils.peekable_iterator import PeekableIterator

class PeekableIteratorTest(TestCase):
    def test_full_iteration(self):
        objects = [object() for i in range(10)]
        it = PeekableIterator(objects)
        for i, x in enumerate(it):
            self.assertIs(x, objects[i])
            for peek_num in range(3): # no matter how many times we peek, we get the same result
                if i == len(objects) - 1:
                    self.assertFalse(it.has_next())
                    with self.assertRaises(StopIteration):
                        it.peek()
                    self.assertIsNone(it.peek_or_none())
                else:
                    self.assertTrue(it.has_next())
                    self.assertIs(it.peek(), objects[i+1])
                    self.assertIs(it.peek_or_none(), objects[i+1])
