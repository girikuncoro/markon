import requests
import logging

from urllib.parse import urljoin

log = logging.getLogger(__name__)


class MissingArgumentException(Exception):
    def __init__(self, arg):
        self.message = 'Missing required argument: {}'.format(arg)


class ConfluenceAPI():
    def __init__(
        self,
        api_url=None,
        username=None,
        password=None,
        _client=None
    ):
        if not api_url.endswith('/'):
            api_url = api_url + '/'
        self.api_url = api_url

        self.username = username
        self.password = password

        if not _client:
            _client = requests.Session()

        self._session = _client
        self._session.auth = (self.username, self.password)

    def _require_kwargs(self, kwargs):
        missing = []
        for k, v in kwargs.items():
            if not v:
                missing.append(k)
        if missing:
            raise MissingArgumentException(missing)

    def _request(
        self,
        method='GET',
        path='',
        params=None,
        data=None
    ):
        url = urljoin(self.api_url, path)
        headers = {}

        if data:
            headers.update({'Content-Type': 'application/json'})

        response = self._session.request(method=method,
                                         url=url,
                                         params=params,
                                         json=data,
                                         headers=headers)

        if not response.ok:
            log.info('''{method} {url}: {status_code} {reason}
            Params: {params}
            Data: {data}'''.format(method=method,
                                   url=url,
                                   status_code=response.status_code,
                                   reason=response.reason,
                                   params=params,
                                   data=data))
            print(response.content)
            return response.content

        return response.json()

    def get(self, path=None, params=None):
        return self._request(method='GET', path=path, params=params)

    def post(self, path=None, params=None, data=None):
        return self._request(method='POST', path=path, params=params, data=data)

    def put(self, path=None, params=None, data=None):
        return self._request(method='PUT', path=path, params=params, data=data)

    def exists(self, space=None, slug=None, ancestor_id=None):
        self._require_kwargs({'slug': slug})

        cql_args = []
        if slug:
            cql_args.append('label={}'.format(slug))
        if ancestor_id:
            cql_args.append('ancestor={}'.format(ancestor_id))
        if space:
            cql_args.append('space={!r}'.format(space))

        cql = ' and '.join(cql_args)

        params = {'expand': 'version', 'cql': cql}
        response = self.get(path='content/search', params=params)
        if not response.get('size'):
            return None
        print(response)
        return response['results'][0]

    def create_labels(self, page_id=None, slug=None, tags=[]):
        labels = [{'name': slug}]
        # TODO: populate tags if given
        path = 'content/{page_id}/label'.format(page_id=page_id)
        response = self.post(path=path, data=labels)

        labels = response.get('results', [])
        if not labels:
            log.error('No labels found after updating page {}'.format(slug))
            print(response)
            return labels

        if not any(label['name'] == slug for label in labels):
            log.error('Label is missing expected slug: {}'.format(slug))
            print(labels)
            return labels

        log.info('Created following labels for page {slug}: {labels}'.format(
            slug=slug,
            labels=', '.join(label['name'] for label in labels)
        ))
        return labels

    def _create_page_payload(
        self,
        content=None,
        title=None,
        ancestor_id=None,
        space=None,
        type='page'
    ):
        return {
            'type': type,
            'title': title,
            'space': {
                'key': space
            },
            'body': {
                'storage': {
                    'representation': 'storage',
                    'value': content
                }
            },
            'ancestors': [{
                'id': str(ancestor_id)
            }]
        }

    def create(
        self,
        content=None,
        space=None,
        title=None,
        ancestor_id=None,
        slug=None,
        type='page'
    ):
        self._require_kwargs({
            'content': content,
            'slug': slug,
            'title': title,
            'space': space,
            'ancestor_id': ancestor_id
        })

        page = self._create_page_payload(content='Creating/updating page in progress...',
                                         title=title,
                                         ancestor_id=ancestor_id,
                                         space=space,
                                         type=type)
        response = self.post(path='content/', data=page)

        page_id = response['id']
        page_url = urljoin(self.api_url, response['_links']['webui'])

        log.info('Page "{title}" (id {page_id}) created successfully at {url})'.format(
            title=title, page_id=response.get('id'), url=page_url))

        return self.update(
            page_id=page_id,
            content=content,
            space=space,
            title=title,
            ancestor_id=ancestor_id,
            slug=slug,
            page=response
        )

    def update(
        self,
        page_id=None,
        content=None,
        space=None,
        title=None,
        ancestor_id=None,
        slug=None,
        page=None,
        type='page'
    ):
        self._require_kwargs({
            'content': content,
            'slug': slug,
            'title': title,
            'page_id': page_id,
            'space': space
        })

        new_page = self._create_page_payload(content=content,
                                             title=title,
                                             ancestor_id=ancestor_id,
                                             space=space,
                                             type=type)

        new_version = page['version']['number'] + 1
        new_page['version'] = {'number': new_version}

        path = 'content/{}'.format(page['id'])
        response = self.put(path=path, data=new_page)
        print(response)

        page_url = urljoin(
            self.api_url,
            response['_links']['context'] + response['_links']['webui']
        )

        self.create_labels(page_id=page_id, slug=slug)

        log.info('Page "{title}" (id {page_id}) updated successfully at {url}'.format(
            title=title, page_id=page_id, url=page_url))
