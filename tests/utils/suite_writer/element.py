import itertools

_id_allocator = itertools.count()


class Element:
    def __init__(self, suite):
        super().__init__()
        self.suite = suite
        self.id = f"{next(_id_allocator):05}"

    def __repr__(self):
        return f"<{type(self).__name__} {self.id}>"
