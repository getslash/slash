from docutils import nodes
from docutils.parsers.rst import directives
from slash import hooks
from slash.utils.callback import Callback

from sphinx.util.compat import Directive

class HookListDoc(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    def run(self):
        returned = []
        all_hooks = []
        for hook_name in dir(hooks):
            hook = getattr(hooks, hook_name)
            if not isinstance(hook, Callback):
                continue
            all_hooks.append((hook_name, hook))
        all_hooks.sort(key=lambda (_, hook) : hook.declaration_index)
        for hook_name, hook in all_hooks:
            section = nodes.section(ids=[hook_name])
            returned.append(section)
            section.append(nodes.title(text="slash.hooks.{0}".format(hook_name)))
            section.append(nodes.paragraph(text=hook.doc))
        return returned

def setup(app):
    directives.register_directive('hook_list_doc', HookListDoc)

