from docutils import nodes
from docutils.parsers.rst import directives
from slash import hooks
import gossip

from sphinx.util.compat import Directive

class HookListDoc(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    def run(self):
        returned = []
        all_hooks = []
        for hook in sorted(gossip.get_group("slash").get_hooks(), key=lambda hook:hook.name):
            section = nodes.section(ids=[hook.name])
            returned.append(section)
            title = "slash.hooks.{0}".format(hook.name)
            args = hook.get_argument_names()
            if args:
                title += "({0})".format(", ".join(args))
            section.append(nodes.title(text=title))
            section.append(nodes.paragraph(text=hook.doc))
        return returned

def setup(app):
    directives.register_directive('hook_list_doc', HookListDoc)

