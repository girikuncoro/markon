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
            headers.update({'Content-Type': 'applicatoin/json'})

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

        params = {'cql': cql}
        response = self.get(path='content/search', params=params)
        if not response.get('size'):
            return None
        return response['results'][0]
