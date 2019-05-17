
import pickle
import pytest

import gcloud.aio.auth.utils as utils  # pylint: disable=unused-import


@pytest.mark.parametrize("str_or_bytes", ['Hello Test', 'UTF-8 Bytes'.encode('utf-8'),
                                          pickle.dumps([])])
def test_encode_decode(str_or_bytes):
  encoded = utils.encode(str_or_bytes)
  expected = str_or_bytes
  if isinstance(expected, bytes):
    try:
        expected = str_or_bytes.decode('utf-8')
    except UnicodeDecodeError:
        pass
  assert expected == utils.decode(encoded)


