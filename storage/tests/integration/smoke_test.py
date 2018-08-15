import os

import aiohttp
import pytest
from gcloud.aio.storage import Storage


@pytest.mark.asyncio
async def test_object_is_downloaded():
    project = os.environ['GCLOUD_PROJECT']
    creds = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

    bucket_name = 'talkiq-integration-transcripts'
    call_id = '07fbe0cc-7f87-1235-06b0-0cc47a392728'
    side = 'callee'
    link = 0
    object_name = f'{call_id}/{side}/{link}/rtp.pcap.wav.ctm'

    async with aiohttp.ClientSession() as session:
        storage = Storage(project, creds, session=session)
        bucket = storage.get_bucket(bucket_name)
        blob = await bucket.get_blob(object_name)
        contructed_result = await blob.download_as_string()

    assert contructed_result

    async with aiohttp.ClientSession() as session:
        storage = Storage(project, creds, session=session)
        direct_result = await storage.download_as_string(bucket_name,
                                                         object_name)

    assert direct_result
    assert contructed_result == direct_result
