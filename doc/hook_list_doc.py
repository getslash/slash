from docutils import nodes
from docutils.parsers.rst import directives, Directive
import gossip


class HookListDoc(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 0

    def run(self):
        returned = []
        for hook in sorted(gossip.get_group("slash").get_hooks(), key=lambda hook: hook.name):
            section = nodes.section(ids=[hook.name], names=[f"hooks.{hook.name}"])
            self.state.document.note_explicit_target(section)
            returned.append(section)
            title = f"slash.hooks.{hook.name}"
            args = hook.get_argument_names()
            if args:
                title += "({})".format(", ".join(args))
            section.append(nodes.title(text=title))
            section.append(nodes.paragraph(text=hook.doc))
        return returned


def setup(app):  # pylint: disable=unused-argument
    directives.register_directive("hook_list_doc", HookListDoc)
