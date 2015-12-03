from contextlib import contextmanager

import requests
import json


__all__ = [
    'activate_pyopenssl_for_urllib3',
]


def activate_pyopenssl_for_urllib3():
    """
    Workaround issue described here:
    https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning

    """
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()


class delayed_request(object):
    """Build streamed file-like instances from an HTTP request.
    """
    def __init__(self, url, method='GET', **kwargs):
        """
        :param basestring url:
          Resource URL

        :param basestring method:
          HTTP method

        :param dict kwargs:
          Optional parameters given to the `requests.sessions.Session.request`
          member method.
        """
        self.__url = url
        self.__method = method
        self.__kwargs = kwargs.copy()

    @contextmanager
    def open(self, session=None):
        """
        :param requests.Session session:
          Optional requests session


        :return:
          file-like object over the decoded bytes
        """
        self.__kwargs.update(stream=True)
        session = session or requests
        resp = session.request(self.__method, self.__url, **self.__kwargs)
        try:
            yield resp
        finally:
            resp.close()

    def __repr__(self):
        return json.dumps(self.__kwargs)
