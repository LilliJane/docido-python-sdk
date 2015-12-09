
import copy
from contextlib import contextmanager
import json
import os.path as osp
import shutil
import tempfile

import six

from docido_sdk.core import (
    Component,
    implements,
)
from docido_sdk.toolbox.threading_ext import RWLock
from .api import (
    IndexAPIProcessor,
    IndexAPIProvider,
)
from .errors import IndexAPIError
from docido_sdk.toolbox.decorators import reraise
from docido_sdk.toolbox.http_ext import delayed_request


reraise = reraise(IndexAPIError)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, delayed_request):
            return repr(obj)
        return repr(obj)


class LocalKVProcessor(IndexAPIProcessor):
    """Local thread-safe, `IndexAPIProcessor` persistent storage
    implementation backed by a json file on the local filesystem.
    """

    __lock = RWLock()
    __store = dict()

    def __init__(self, **config):
        """
        :param path: Path to a json file where the KVS is written.
        """
        super(LocalKVProcessor, self).__init__(**config)
        local_storage = config.get('local_storage', {})
        kv_storage = local_storage.get('kv', {})
        path = kv_storage.get('path')
        if path is None:
            path = tempfile.mkdtemp(prefix='docido-local-storage-kv')
        path = osp.join(path, 'kv.yaml')
        self.__path = path
        with self.__lock.write():
            if osp.exists(path):
                with open(path) as istr:
                    self.__store = json.load(istr)

    @reraise
    def get_key(self, key):
        assert isinstance(key, six.string_types)
        with self.__lock.read():
            return self.__store.get(key)

    @reraise
    def get_kvs(self):
        with self.__lock.read():
            return copy.copy(self.__store)

    @reraise
    def set_key(self, key, value):
        assert isinstance(key, six.string_types)
        assert isinstance(value, six.string_types)
        with self.__lock.write():
            self.__store[key] = value
            self.__persist()

    @reraise
    def delete_key(self, key):
        assert isinstance(key, six.string_types)
        with self.__lock.write():
            self.__store.pop(key, None)
            self.__persist()

    @reraise
    def delete_keys(self):
        with self.__lock.write():
            self.__store.clear()
            self.__persist()

    def __persist(self):
        with open(self.__path + '.new', 'w') as ostr:
            json.dump(self.__store, ostr, indent=2, cls=CustomJSONEncoder)
        shutil.move(self.__path + '.new', self.__path)


class LocalKV(Component):
    implements(IndexAPIProvider)

    def get_index_api(self, **config):
        return LocalKVProcessor(**config)


class LocalDumbIndexProcessor(IndexAPIProcessor):
    """Dumb, but yet reentrant, index implementation, persisting indices
    in local-filesystem.

    Some methods does not provide all functionalities the real Docido index
    provides. More information available in documentation of the following
    member methods: `delete_cards`, `search_cards`, and `delete_thumbnails`.
    """
    __lock = RWLock()
    __cards = dict()
    __thumbnails = dict()

    def __init__(self, **config):
        super(LocalDumbIndexProcessor, self).__init__(**config)
        local_storage = config.get('local_storage', {})
        index_storage = local_storage.get('documents', {})
        path = index_storage.get('path')
        if path is None:
            path = tempfile.mkdtemp('docido-local-storage-documents')
        cards_path = osp.join(path, 'cards.yml')
        thumbnails_path = osp.join(path, 'thumbnails.yml')
        failure_probability = index_storage.get('failure_probability', 0)

        self.__cards_path = cards_path
        self.__thumbnails_path = thumbnails_path
        self.__cards = LocalDumbIndexProcessor.load_index(cards_path)
        self.__thumbnails = LocalDumbIndexProcessor.load_index(thumbnails_path)
        self.__failure_probability = failure_probability

    @contextmanager
    def __update(self, cards=False, thumbnails=False):
        self.__lock.writer_acquire()
        try:
            yield
            if cards:
                LocalDumbIndexProcessor.persist_index(
                    self.__cards, self.__cards_path
                )
            if thumbnails:
                LocalDumbIndexProcessor.persist_index(
                    self.__thumbnails,
                    self.__thumbnails_path
                )
        finally:
            self.__lock.writer_release()

    def push_cards(self, cards):
        with self.__update(cards=True):
            for card in cards:
                self.__cards[card['id']] = card

    def delete_cards(self, query=None):
        if query != {'query': {'match_all': {}}}:
            raise IndexAPIError(
                'only match_all query is currently supported, you should use' +
                ' the ElasticSearch processor along with es-settings.yml ' +
                'config file instead'
            )
        with self.__update(cards=True):
            self.__cards.clear()

    def delete_cards_by_id(self, ids):
        errors = []
        with self.__update(cards=True):
            for _id in ids:
                if _id not in self.__cards:
                    errors.append({'status': 404, 'id': _id})
                    continue
                del self.__cards[_id]
            return errors

    def search_cards(self, query=None):
        with self.__lock.read():
            fetch_fields = None
            if query and 'fields' in query.keys():
                fetch_fields = query.get('fields', None)
            result = list()
            if fetch_fields is not None:
                for card in self.__cards.values():
                    result.append(dict((k, card[k]) for k in fetch_fields))
            else:
                for card in self.__cards.values():
                    result.append(card)
        return result
        # return {
        #     'took': 1,
        #     'timed_out': False,
        #     '_shards': {
        #         'total': 1,
        #         'successful': 1,
        #         'failed': 0,
        #     },
        #     'hits': {
        #         'total': len(result),
        #         'max_score': 1.0,
        #         'hits': [{
        #             '_index': 'docido',
        #             '_type': 'item',
        #             '_id': r['id'],
        #             '_score': 1.0,
        #             '_source': r
        #         } for r in result
        #         ],
        #     }
        # }

    def push_thumbnails(self, thumbnails):
        with self.__update(thumbnails=True):
            for id_, payload, mime in thumbnails:
                self.__thumbnails[id_] = (payload, mime)

    def delete_thumbnails(self, query):
        if query != {'query': {'match_all': {}}}:
            raise IndexAPIError(
                'only match_all query is currently supported, you should use' +
                ' the ElasticSearch processor along with es-settings.yml ' +
                'config file instead'
            )
        with self.__update(thumbnails=True):
            self.__thumbnails.clear()

    def delete_thumbnails_by_id(self, ids):
        errors = []
        with self.__update(thumbnails=True):
            for _id in ids:
                if _id not in self.__thumbnails:
                    errors.append({'status': 404, 'id': _id})
                    continue
                del self.__thumbnails[_id]
            return errors

    @classmethod
    def load_index(cls, path):
        if not osp.exists(path):
            return dict()
        else:
            with open(path) as istr:
                return json.load(istr)

    @classmethod
    def persist_index(cls, index, path):
        with open(path + '.new', 'w') as ostr:
            json.dump(index, ostr, indent=2, cls=CustomJSONEncoder)
        shutil.move(path + '.new', path)


class LocalDumbIndex(Component):
    implements(IndexAPIProvider)

    def get_index_api(self, **config):
        return LocalDumbIndexProcessor(**config)
