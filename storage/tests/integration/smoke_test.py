import asyncio
import os

import aiohttp
from gcloud.aio.storage import make_download


async def download_object(project, creds, bucket_name, object_name):
    async with aiohttp.ClientSession() as session:
        download = make_download(project, creds, bucket_name, session=session)
        result = await download(object_name)

    assert result


def test_object_is_downloaded():
    project = os.environ['GCLOUD_PROJECT']
    creds = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

    bucket_name = 'talkiq-integration-transcripts'
    call_id = '07fbe0cc-7f87-1235-06b0-0cc47a392728'
    side = 'callee'
    link = 0
    object_name = f'{call_id}/{side}/{link}/rtp.pcap.wav.ctm'

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        download_object(project, creds, bucket_name, object_name))
