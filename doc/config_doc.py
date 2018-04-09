from docutils.parsers.rst import directives, Directive
from docutils import nodes
from slash.conf import config


class ConfigDoc(Directive):
    required_arguments = 0
    optional_arguments = 0

    def run(self):
        returned = []
        for path, leaf in config.traverse_leaves():
            section = nodes.section(names=["conf." + path])
            self.state.document.note_explicit_target(section)
            section.append(nodes.title(text=path))
            section.append(nodes.strong(text="Default: {}".format(leaf.get_value())))
            if leaf.metadata and "doc" in leaf.metadata:
                section.append(nodes.paragraph(text=str(leaf.metadata["doc"])))
            returned.append(section)
        return returned


def setup(app):                 # pylint: disable=unused-argument
    directives.register_directive('config_doc', ConfigDoc)
