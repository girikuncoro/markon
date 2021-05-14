import yaml

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
