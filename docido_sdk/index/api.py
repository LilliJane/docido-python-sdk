
from docido_sdk.core import Interface

__all__ = [
    'IndexAPI',
    'IndexAPIConfigurationProvider',
    'IndexAPIProcessor',
    'IndexAPIProvider',
    'IndexPipelineConfig',
]


class IndexAPIProvider(Interface):
    """ Provide an implementation of IndexAPI
    """
    def get_index_api(**config):
        """ Create a new instance of :py:class:`docido_sdk.index.IndexAPI`

        :param dict: config:
          extra configuration given to the object to create

        :return: new instance
        :rtype: :py:class:`docido_sdk.index.IndexAPI`
        """


class IndexAPI(object):
    """Read/write access to Docido index.

    :An IndexAPI object can manipulate 3 kind of data:
        :cards:
          a searchable item in Docido index.
        :thumbnails:
          a binary item in Docido index, for thumbnails of
          card's attachments. Used to improve user-experience by providing
          fast preview of binary files attached to cards.
        :a key value store:
          provides crawlers a way to persist their synchronization state.

    :Error Handling:
        Every bulk operation that modifies Docido index returns the list of
        operations that failed. Every item is a `dict` providing
        the following key:

        :status:
          http error code
        :error:
          reason in string format
        :id:
          error identifier
        :card:
          original card

    :Filtering:
        Index enumeration and deletion operations allow you to restrict
        the target scope by providing a `query` in parameter.
        The `query` parameters follows the Elasticsearch Query DSL.
    """
    def push_cards(cards):
        """Send a synchronous bulk indexing request

        :param list cards: collections of cards to index.

        :return: collection of items whose insertion failed.
        """

    def delete_cards(query=None):
        """Send a synchronous bulk deletion request.

        :param list query: a search definition using the Elasticsearch
            Query DSL to restrict the scope of cards to delete.

        :return: collection of items whose deletion failed.
        """

    def search_cards(query=None):
        """Enumerate cards in Docido index.

        :param list query: a search definition using the
            Elasticsearch Query DSL

        :return: FIXME
        """

    def push_thumbnails(thumbnails):
        """Add or update thumbnails in dedicated Docido index.

        :param list thumbnails: Collection of tuples
                                `(identifier, encoded_bytes, mime_type)`

        :return: collection of items whose insertion failed.
        """

    def delete_thumbnails(query=None):
        """Delete thumbnails from dedicated Docido index.

        :param query: a search definition using the Elasticsearch Query DSL to
                    restrict the scope of thumbnails to delete.

        :return: collection of items whose deletion failed.
        """

    def get_kv(key):
        """Retrieve value from persistence layer

        :param string key: input key

        :return: the value is present, `None` otherwise.
        :rtype: string
        """

    def set_kv(key, value):
        """Insert or update existing key in persistence layer.

        :param string key: input key
        :param string value: value to store
        """

    def delete_kv(key):
        """Remove key from persistent storage.

        :param key: the key to remove
        """

    def delete_kvs():
        """Remove all crawler persisted data.
        """

    def get_kvs():
        """Retrieve all crawler persisted data.

        :return: collection of tuple `(key, value)`
        :rtype: list
        """

    def ping():
        """Test availability of Docido index

        :raises SystemError: if Docido index is unreachable
        """

    def refresh_oauth_access_token():
        """Refresh OAuth access token.
        This method may be used when the crawled source
        invalidates the OAuth access token.

        :return: new access token
        :rtype: basestring
        """


class IndexAPIProcessor(IndexAPI):
    """ Allows creation of :py:class:`docido_sdk.index.IndexAPI` pipelines
    """
    def __init__(self, parent=None, **config):
        """
        :param :py:class:`docido_sdk.index.IndexAPI`: parent:
          next pipeline object

        :param dict: config:
          extra processor configuration
        """
        self._parent = parent
        self._config = config

    def push_cards(self, cards):
        return self._parent.push_cards(cards)

    def delete_cards(self, query=None):
        return self._parent.delete_cards(query)

    def search_cards(self, query=None):
        return self._parent.search_cards(query)

    def push_thumbnails(self, thumbnails):
        return self._parent.push_thumbnails(thumbnails)

    def delete_thumbnails(self, query=None):
        return self._parent.delete_thumbnails(query)

    def get_kv(self, key):
        return self._parent.get_kv(key)

    def set_kv(self, key, value):
        return self._parent.set_kv(key, value)

    def delete_kv(self, key):
        return self._parent.delete_kv(key)

    def delete_kvs(self):
        return self._parent.delete_kvs()

    def get_kvs(self):
        return self._parent.get_kvs()

    def ping(self):
        return self._parent.ping()


class IndexAPIConfigurationProvider(Interface):
    """ An interface to provide a configuration consumed by
    :py:class:`docido_sdk.index.IndexAPIProcessor`
    """
    def get_index_api_conf(service, docido_user_id, account_login):
        """ Provides a configuration object given to every index processors

        :param basestring: service:
          account service name (gmail, trello, ...)

        :param basestring: docido_user_id:
          the Docido user identifier for which the IndexAPI is meant form

        :param basestring: account_login
          the user account login for which the IndexAPI is meant for

        :return: IndexAPI Configuration
        :rtype: dict
        """
        pass


class IndexPipelineConfig(Interface):
    """ Provides list of :py:class:`docido_sdk.index.IndexAPIProvider`
    to link together in order to create the indexing pipeline.
    """
    def get_pipeline():
        """
        :return:
          description of the index pipeline to create
        :rtype: :py:class:`docido_sdk.index.IndexAPIProvider`
        """
        pass
