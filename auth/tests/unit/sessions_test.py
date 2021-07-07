import pytest
from gcloud.aio.auth.build_constants import BUILD_GCLOUD_REST
from gcloud.aio.auth.session import AioSession

if BUILD_GCLOUD_REST:
    import requests

    class Session(requests.Session):
        def __init__(self, *args, **kwargs) -> None:
            self._called = False
            super(requests.Session, self).__init__(*args, **kwargs)

        def close(self) -> None:
            self._called = True
            super(requests.Session, self).close()

        @property
        def closed(self) -> bool:
            return self._called

    requests.Session = Session
else:
    from aiohttp import ClientSession as Session


@pytest.mark.asyncio
async def test_unmanaged_session():
    async with Session() as session:
        gcloud_session = AioSession(session=session)
        assert gcloud_session._shared_session  # pylint: disable=protected-access
        await gcloud_session.close()

        assert not session.closed


@pytest.mark.asyncio
async def test_managed_session():
    gcloud_session = AioSession()
    internal_session = gcloud_session.session
    assert not gcloud_session._shared_session  # pylint: disable=protected-access
    await gcloud_session.close()

    assert internal_session.closed
