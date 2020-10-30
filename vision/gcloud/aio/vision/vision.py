import io
import json
import logging
from typing import Dict, List, Optional, Union

from gcloud.aio.auth import (
    AioSession,
    BUILD_GCLOUD_REST,
    Token,
)
from gcloud.aio.vision import AnnotateImageRequest

# Selectively load libraries based on the package
if BUILD_GCLOUD_REST:
    from requests import Session
else:
    from aiohttp import ClientSession as Session

API_ROOT = "https://vision.googleapis.com/v1"

SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/cloud-vision",
]

log = logging.getLogger(__name__)


class Vision:
    def __init__(
        self,
        service_file: Optional[Union[str, io.IOBase]] = None,
        session: Optional[Session] = None,
        token: Optional[Token] = None,
    ) -> None:

        self.session = AioSession(session)
        self.token = token or Token(
            service_file=service_file, session=self.session.session, scopes=SCOPES
        )

    async def headers(self) -> Dict[str, str]:
        token = await self.token.get()
        return {
            "Authorization": f"Bearer {token}",
        }

    # https://cloud.google.com/vision/docs/reference/rest/v1/images/annotate
    async def image_annotate(
        self,
        requests: List[AnnotateImageRequest],
        session: Optional[Session] = None,
        timeout: int = 10,
    ) -> Union[List, Dict]:
        url = f"{API_ROOT}/images:annotate"

        payload = json.dumps(
            {"requests": [request.to_dict() for request in requests]}
        ).encode("utf-8")

        headers = await self.headers()
        headers.update(
            {"Content-Length": str(len(payload)), "Content-Type": "application/json"}
        )

        s = AioSession(session) if session else self.session
        resp = await s.post(url, data=payload, headers=headers, timeout=timeout)
        data = await resp.json()

        return data
