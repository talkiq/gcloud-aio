import json
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from gcloud.aio.datastore import Datastore


# pylint: disable=protected-access
class TestPost:
    @staticmethod
    async def test_no_body_no_additional_fields(mocker):
        ds = Datastore(project='test-project')
        mocker.patch.object(ds, 'headers', return_value={})
        mock_resp = AsyncMock()
        ds.session = MagicMock()
        ds.session.post = AsyncMock(return_value=mock_resp)

        result = await ds._post('https://example.com')

        ds.session.post.assert_called_once_with(
            'https://example.com',
            headers={
                'Content-Type': 'application/json',
                'Content-Length': '0'},
            timeout=10.,
        )
        assert result is mock_resp

    @staticmethod
    async def test_body_only(mocker):
        ds = Datastore(project='test-project')
        mocker.patch.object(ds, 'headers', return_value={})
        mock_resp = AsyncMock()
        ds.session = MagicMock()
        ds.session.post = AsyncMock(return_value=mock_resp)
        body = {'key': 'value'}

        result = await ds._post('https://example.com', body)

        expected_payload = json.dumps(body).encode('utf-8')
        ds.session.post.assert_called_once_with(
            'https://example.com',
            data=expected_payload,
            headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(expected_payload)),
            },
            timeout=10.,
        )
        assert result is mock_resp

    @staticmethod
    async def test_additional_request_fields_only(mocker):
        ds = Datastore(project='test-project')
        mocker.patch.object(ds, 'headers', return_value={})
        mock_resp = AsyncMock()
        ds.session = MagicMock()
        ds.session.post = AsyncMock(return_value=mock_resp)
        extra = {'customField': 'customValue'}

        result = await ds._post(
            'https://example.com',
            additional_request_fields=extra,
        )

        expected_payload = json.dumps(extra).encode('utf-8')
        ds.session.post.assert_called_once_with(
            'https://example.com',
            data=expected_payload,
            headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(expected_payload)),
            },
            timeout=10.,
        )
        assert result is mock_resp

    @staticmethod
    async def test_body_and_additional_fields_merged(mocker):
        """additional_request_fields wins on key collision."""
        ds = Datastore(project='test-project')
        mocker.patch.object(ds, 'headers', return_value={})
        mock_resp = AsyncMock()
        ds.session = MagicMock()
        ds.session.post = AsyncMock(return_value=mock_resp)
        body = {'a': 1, 'b': 2}
        extra = {'b': 99, 'c': 3}

        await ds._post(
            'https://example.com', body,
            additional_request_fields=extra,
        )

        expected_payload = json.dumps(
            {'a': 1, 'b': 99, 'c': 3}).encode('utf-8')
        ds.session.post.assert_called_once_with(
            'https://example.com',
            data=expected_payload,
            headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(expected_payload)),
            },
            timeout=10.,
        )

    @staticmethod
    async def test_no_session_uses_self_session(mocker):
        ds = Datastore(project='test-project')
        mocker.patch.object(ds, 'headers', return_value={})
        mock_session = MagicMock()
        mock_session.post = AsyncMock()
        ds.session = mock_session

        await ds._post('https://example.com', {'x': 1})

        mock_session.post.assert_called_once()

    @staticmethod
    async def test_provided_session_is_wrapped_in_aio_session(mocker):
        ds = Datastore(project='test-project')
        mocker.patch.object(ds, 'headers', return_value={})
        raw_session = MagicMock()
        mock_wrapped = MagicMock()
        mock_wrapped.post = AsyncMock()

        with patch(
            'gcloud.aio.datastore.datastore.AioSession',
            return_value=mock_wrapped,
        ) as mock_aio_cls:
            await ds._post(
                'https://example.com', {'x': 1},
                session=raw_session,
            )

        mock_aio_cls.assert_called_once_with(raw_session)
        mock_wrapped.post.assert_called_once()
