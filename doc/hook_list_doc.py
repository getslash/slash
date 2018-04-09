from docutils import nodes
from docutils.parsers.rst import directives, Directive
from slash import hooks  # pylint: disable=unused-import
import gossip


class HookListDoc(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    def run(self):
        returned = []
        for hook in sorted(gossip.get_group("slash").get_hooks(), key=lambda hook: hook.name):
            section = nodes.section(ids=[hook.name], names=['hooks.{}'.format(hook.name)])
            self.state.document.note_explicit_target(section)
            returned.append(section)
            title = "slash.hooks.{}".format(hook.name)
            args = hook.get_argument_names()
            if args:
                title += "({})".format(", ".join(args))
            section.append(nodes.title(text=title))
            section.append(nodes.paragraph(text=hook.doc))
        return returned

def setup(app):  # pylint: disable=unused-argument
    directives.register_directive('hook_list_doc', HookListDoc)
