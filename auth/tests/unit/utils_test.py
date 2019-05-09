import gcloud.aio.auth.utils as utils  # pylint: disable=unused-import


def test_importable():
    assert True


def test_is_base64_encoded():
  assert utils.valid_base64('')
  assert utils.valid_base64('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890=+/')

  assert not utils.valid_base64('ABC~abc')
  assert not utils.valid_base64('%')

  assert utils.valid_base64(utils.encode('ABC~abc'))
