# markon

Sync markdown files with Confluence pages.

This project was originally created to sync Docusaurus docs to Confluence as part of the CI pipelines.

## Quick Start

Before using the project, you have to install the Python dependencies:
```bash
pip install -r requirements.txt
```
Then, you can run the script:
```bash
markon.py --api-url ${CONFLUENCE_API_URL} \
  --username ${CONFLUENCE_USERNAME} \
  --password ${CONFLUENCE_PASSWORD} \
  --space ${CONFLUENCE_SPACE} \
  --ancestor-id ${CONFLUENCE_ANCESTOR_ID} \
  ${DOCS_FILE_PATH}
```

Or just simply run using docker:
```bash
docker run -v $(pwd):/docs \
  -e CONFLUENCE_API_URL=${CONFLUENCE_API_URL} \
  -e CONFLUENCE_USERNAME=${CONFLUENCE_USERNAME} \
  -e CONFLUENCE_PASSWORD=${CONFLUENCE_PASSWORD} \
  girikuncoro/markon:latest python markon.py ${DOCS_FILE_PATH}
```

## Usage

```bash
usage: markon.py [-h] [--api-url API_URL] [--username USERNAME]
                 [--password PASSWORD] [--space SPACE]
                 [--ancestor-id ANCESTOR_ID]
                 [--attachment-static-path ATTACHMENT_STATIC_PATH]
                 [pages [pages ...]]

Markon - a tool for updating Atlassian Confluence pages from markdown

positional arguments:
  pages                 Markdown pages to sync into confluence pages

optional arguments:
  -h, --help            show this help message and exit
  --api-url API_URL     URL pointing to Confluence API
  --username USERNAME   Username for authentication to Confluence API
  --password PASSWORD   Password for authentication to Confluence API, can
                        also be API token
  --space SPACE         Confluence space where the markdown file should reside
  --ancestor-id ANCESTOR_ID
                        Confluence id of parent page to put the markdown file
                        under
  --attachment-static-path ATTACHMENT_STATIC_PATH
                        The path of static folder where images and assets of
                        attachments are stored
```

## What to Write in your Markdown Files

This project needs the Markdown files to have metadata (or in Markdown convention called [front-matter](https://jekyllrb.com/docs/front-matter/)) at the top.
In order for file to be processed by `markon`, you need to have the following metadata in your file:
```bash
confluence:
  share: true
```

You can also include the space and ancestor id in the metadata, so that you don't have to give it via flags:
```bash
confluence:
  share: true
  space: FOO
  ancestor_id: 1234
```

## Tips on Running from your CI Pipelines

It's quite trivial to integrate `markon` into a CI/CD system, here's an example:
```bash
stage: docs:sync

docs:sync:
  image: girikuncoro/markon:latest
  stage: docs:sync
  script:
    - |
      for file in $(find -type f -name '*.md'); do
        echo "> Sync $file";
        /app/markon.py $file || exit 1;
        echo;
      done
```
