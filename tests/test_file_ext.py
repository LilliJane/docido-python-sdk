import pickle
import unittest
import json
import mock
import __builtin__

from docido_sdk.toolbox.file_ext import iterator_to_file
from docido_sdk.toolbox.http_ext import delayed_request
from docido_sdk.index.test import CustomJSONEncoder


class TestStreamFromRequest(unittest.TestCase):
    def test_pickle(self):
        s = delayed_request('http://google.com')
        json.dumps(repr(s))
        pickle.dumps(s)

    def test_json(self):
        s = delayed_request('http://google.com', param=dict(test='test'))
        self.assertEqual(
            '"{\\"param\\": {\\"test\\": \\"test\\"}}"',
            json.dumps(s, cls=CustomJSONEncoder)
        )
        with mock.patch.object(__builtin__, 'repr',
                               return_value=None) as test:
            CustomJSONEncoder().default('Test')
        test.assert_called_once_with('Test')

    def test_fetch_google(self):
        with delayed_request('http://google.com').open() as istr:
            istr = iterator_to_file(iter(istr))
            all_content = content = istr.read(50)
            while len(content) == 50:
                content = istr.read(50)
                all_content += content
        self.assertTrue(all_content.endswith('</body></html>'))

        with delayed_request('http://google.com').open() as istr:
            istr = iterator_to_file(iter(istr))
            all_content_at_once = istr.read()
        self.assertTrue(all_content_at_once.endswith('</body></html>'))


if __name__ == '__main__':
    unittest.main()
