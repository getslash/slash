from docutils import nodes
from docutils.parsers.rst import directives
from shakedown.conf import config

from sphinx.util.compat import Directive


class ConfigDoc(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    def run(self):
        returned = []
        for path, leaf in config.traverse_leaves():
            p = nodes.paragraph()
            returned.append(p)
            p.append(nodes.strong(text=path))
            if leaf.metadata and "doc" in leaf.metadata:
                p.append(nodes.paragraph(text=str(leaf.metadata["doc"])))
        return returned

def setup(app):
    directives.register_directive('config_doc', ConfigDoc)

