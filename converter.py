import yaml
import mistune
import textwrap
import os
from urllib.parse import urlparse

YAML_END = '---'


def parse(page_path):
    raw_yaml = ''
    markdown = ''
    in_yaml = True
    with open(page_path, 'r') as page:
        for line in page.readlines():
            if line.strip() == YAML_END:
                if in_yaml and raw_yaml:
                    in_yaml = False
                    continue
            if in_yaml:
                raw_yaml += line
            else:
                markdown += line
    metadata = yaml.load(raw_yaml, Loader=yaml.SafeLoader)
    markdown = markdown.strip()
    return metadata, markdown


def convert_to_confluence(markdown, metadata={}):
    renderer = ConfluenceRenderer()
    content_html = mistune.markdown(markdown, renderer=renderer)
    page_html = renderer.layout(content_html)

    return page_html, renderer.attachments


class ConfluenceRenderer(mistune.Renderer):
    def __init__(self):
        self.attachments = []
        super().__init__()

    def layout(self, content):
        toc = textwrap.dedent('''
            <h1>Table of Contents</h1>
            <p><ac:structured-macro ac:name="toc" ac:schema-version="1">
                <ac:parameter ac:name="exclude">^(Authors|Table of Contents)$</ac:parameter>
            </ac:structured-macro></p>''')
        column = textwrap.dedent('''
            <ac:structured-macro ac:name="column" ac:schema-version="1">
                <ac:parameter ac:name="width">{width}</ac:parameter>
                <ac:rich-text-body>{content}</ac:rich-text-body>
            </ac:structured-macro>''')
        sidebar = column.format(width='30%', content=toc)
        main_content = column.format(width='800px', content=content)
        return sidebar + main_content

    def image(self, src, title, alt_text):
        is_external = bool(urlparse(src).netloc)
        tag_template = '<ac:image>{image_tag}</ac:image>'
        image_tag = '<ri:url ri:value="{}" />'.format(src)
        if not is_external:
            image_tag = '<ri:attachment ri:filename="{}" />'.format(
                os.path.basename(src))
            self.attachments.append(src)
        return tag_template.format(image_tag=image_tag)
