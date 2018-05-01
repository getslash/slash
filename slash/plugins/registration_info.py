class RegistrationInfo(object):

    def __init__(self, hook_name, expect_exists, register_kwargs=None):
        assert isinstance(expect_exists, bool)
        self.hook_name = hook_name
        self.expect_exists = expect_exists
        self.register_kwargs = register_kwargs or {}
