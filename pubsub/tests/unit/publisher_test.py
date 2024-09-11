from typing import Optional
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from gcloud.aio.pubsub import PublisherClient

# =========
# client
# =========


class _MockToken:
    @staticmethod
    async def get() -> Optional[str]:
        return 'Unit-Test-Bearer-Token'


@pytest.mark.asyncio
async def test_client_api_is_dev():
    """
    Test that the api_is_dev constructor parameter controls whether the
    Authorization header is set on requests
    """
    async def _make_request(client_obj: PublisherClient,
                            should_have_auth_header: bool) -> None:
        with patch.object(
                client_obj.session, 'put', return_value=AsyncMock(),
        ) as mock_req:
            async with client_obj as client:
                await client.create_topic('foobar')
        assert mock_req.call_count == 1
        assert (
            'Authorization' in mock_req.mock_calls[0].kwargs['headers']
        ) == should_have_auth_header

    api_root = 'https://foobar/v1'

    # With no API root specified, assume API not dev, so auth header should be
    # set
    await _make_request(
        PublisherClient(token=_MockToken()), should_have_auth_header=True,
    )
    # If API root set and not otherwise specified, assume API is dev, so auth
    # header should not be set
    await _make_request(
        PublisherClient(api_root=api_root, token=_MockToken()),
        should_have_auth_header=False,
    )
    # If API specified to be dev, auth header should not be set
    await _make_request(
        PublisherClient(api_root=api_root, api_is_dev=True,
                        token=_MockToken()),
        should_have_auth_header=False,
    )
    # If API specified to not be dev, auth header should be set
    await _make_request(
        PublisherClient(
            api_root=api_root,
            api_is_dev=False,
            token=_MockToken()),
        should_have_auth_header=True,
    )
