#!/usr/bin/env python3
import sys
import os
import argparse
import logging

from confluence_api import ConfluenceAPI
from converter import parse

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = ['.md']


def parse_args():
    parser = argparse.ArgumentParser(
        description='Markon - a tool for updating Atlassian Confluence pages from markdown'
    )
    parser.add_argument(
        '--api-url',
        dest='api_url',
        default=os.getenv('CONFLUENCE_API_URL'),
        help='URL pointing to Confluence API'
    )
    parser.add_argument(
        '--username',
        dest='username',
        default=os.getenv('CONFLUENCE_USERNAME'),
        help='Username for authentication to Confluence API'
    )
    parser.add_argument(
        '--password',
        dest='password',
        default=os.getenv('CONFLUENCE_PASSWORD'),
        help='Password for authentication to Confluence API, can also be API token'
    )
    parser.add_argument(
        '--space',
        dest='space',
        default=os.getenv('CONFLUENCE_SPACE'),
        help='Confluence space where the markdown file should reside'
    )
    parser.add_argument(
        '--ancestor-id',
        dest='ancestor_id',
        default=os.getenv('CONFLUENCE_ANCESTOR_ID'),
        help='Confluence id of parent page to put the markdown file under'
    )
    parser.add_argument(
        'pages',
        type=str,
        nargs='*',
        help='Markdown pages to sync into confluence pages'
    )

    args = parser.parse_args()

    if not args.api_url:
        log.error('Please provide valid API URL')
        sys.exit(1)

    return parser.parse_args()


def get_slug(filepath):
    slug, _ = os.path.splitext(os.path.basename(filepath))
    slug = slug.replace('-', '_')
    return slug


def create_or_update_page(page_path, args, confluence_api):
    _, ext = os.path.splitext(page_path)
    if ext not in SUPPORTED_EXTENSIONS:
        log.info('Skipping {} since not a supported format'.format(page_path))
        return

    try:
        metadata, markdown = parse(page_path)
    except Exception as e:
        log.error('Error when processing {}: {}'.format(page_path, e))
        return

    if 'confluence' not in metadata or not metadata['confluence'].get('share'):
        log.info('Page {} not set to be uploaded to Confluence'.format(page_path))
        return

    # TODO: Check author from metadata and confluence

    # TODO: Add attachments
    # html = convert_to_confluence(markdown, metadata=metadata)
    html = '<p>Test content created from markon</p>'

    page_slug = get_slug(page_path)

    ancestor_id = metadata['confluence'].get('ancestor_id', args.ancestor_id)
    space = metadata['confluence'].get('space', args.space)

    # TODO: Check confluence page exists
    # page = confluence_api.exists()
    page = confluence_api.exists(
        slug=page_slug,
        ancestor_id=ancestor_id,
        space=space
    )

    if page:
        confluence_api.update(page['id'],
                              content=html,
                              title=metadata['title'],
                              slug=page_slug,
                              space=space,
                              ancestor_id=ancestor_id,
                              page=page)
    else:
        confluence_api.create(content=html,
                              title=metadata['title'],
                              slug=page_slug,
                              space=space,
                              ancestor_id=ancestor_id)


def main():
    args = parse_args()

    confluence_api = ConfluenceAPI(api_url=args.api_url,
                                   username=args.username,
                                   password=args.password)

    changed_pages = []
    if args.pages:
        changed_pages = [os.path.abspath(page) for page in args.pages]
        for page_path in changed_pages:
            if not os.path.exists(page_path) or not os.path.isfile(page_path):
                log.error('File {} do not exists'.format(page_path))
                sys.exit(1)

    if not changed_pages:
        log.info('No page created/modified')
        return

    for page in changed_pages:
        log.info('Creating or updating {}'.format(page))
        create_or_update_page(page, args, confluence_api)


if __name__ == '__main__':
    main()
