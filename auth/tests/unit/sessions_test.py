import pytest
from aiohttp import ClientSession
from gcloud.aio.auth.session import AioSession


@pytest.mark.asyncio
async def test_unmanaged_session():
    async with ClientSession() as session:
        aio_session = AioSession(session=session)
        assert aio_session._shared_session  # pylint: disable=protected-access
        await aio_session.close()

        assert not session.closed


@pytest.mark.asyncio
async def test_managed_session():
    aio_session = AioSession()
    internal_session = aio_session.session
    assert not aio_session._shared_session  # pylint: disable=protected-access
    await aio_session.close()
    assert internal_session.closed
