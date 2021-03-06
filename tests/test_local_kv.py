from contextlib import contextmanager
import copy
import os.path as osp
import shutil
import tempfile
import unittest

from docido_sdk.env import Environment
from docido_sdk.index import (
    IndexAPIConfigurationProvider,
    IndexAPIError,
    IndexPipelineConfig,
)
from docido_sdk.index.pipeline import IndexPipelineProvider
from docido_sdk.index.test import LocalKV
from docido_sdk.core import (
    Component,
    ComponentMeta,
    implements,
)
from docido_sdk.toolbox.contextlib_ext import unregister_component


class TestLocalKV(unittest.TestCase):
    @contextmanager
    def push_env(self):
        components = copy.copy(ComponentMeta._components)
        registry = copy.copy(Component._registry)
        try:
            yield
        finally:
            ComponentMeta._components = components
            ComponentMeta._registry = registry

    @contextmanager
    def kv(self):
        from docido_sdk.index.config import YamlPullCrawlersIndexingConfig
        with unregister_component(YamlPullCrawlersIndexingConfig):
            env = Environment()
            env.temp_dir = tempfile.mkdtemp()

            class ForcePipeline(Component):
                implements(IndexPipelineConfig)

                def get_pipeline(self):
                    return [env[LocalKV]]

            class ForceConfig(Component):
                implements(IndexAPIConfigurationProvider)

                def get_index_api_conf(self, service,
                                       docido_user_id, account_login):
                    return {
                        'local_storage': {
                            'documents': {
                                'path': env.temp_dir,
                            },
                            'kv': {
                                'path': env.temp_dir,
                            },
                        },
                    }
            env[ForcePipeline]
            env[ForceConfig]
            pipeline = env[IndexPipelineProvider]
            try:
                yield pipeline.get_index_api(None, None, None)
            finally:
                ForcePipeline.unregister()
                ForceConfig.unregister()
                if osp.isdir(env.temp_dir):
                    shutil.rmtree(env.temp_dir)

    def test_kv(self):
        with self.kv() as kv:
            key = 'key'
            self.assertIsNone(kv.get_key(key))
            kv.set_key(key, 'value1')
            self.assertEqual(kv.get_key(key), 'value1')
            kv.delete_key(key)
            self.assertIsNone(kv.get_key(key))
            kvs = dict([('key' + str(i), 'value' + str(i))
                       for i in range(1, 4)])
            for k, v in kvs.iteritems():
                kv.set_key(k, v)
            inserted_kvs = dict(kv.get_kvs())
            self.assertEqual(kvs, inserted_kvs)
            kv.delete_keys()
            self.assertEqual({}, kv.get_kvs())

    def test_key_is_None(self):
        with self.kv() as kv:
            with self.assertRaises(IndexAPIError):
                kv.get_key(None)
            with self.assertRaises(IndexAPIError):
                kv.set_key(None, 'value1')
            with self.assertRaises(IndexAPIError):
                kv.delete_key(None)

    def test_value_is_None(self):
        with self.kv() as kv:
            with self.assertRaises(IndexAPIError):
                kv.set_key('key', None)

if __name__ == '__main__':
    unittest.main()
