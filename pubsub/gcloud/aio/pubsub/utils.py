from typing import Any
from typing import Dict
from typing import Union

from gcloud.aio.auth import encode  # pylint: disable=no-name-in-module


# https://cloud.google.com/pubsub/docs/reference/rest/v1/PubsubMessage
class PubsubMessage:
    def __init__(self, data: Union[bytes, str], ordering_key: str = '',
                 **kwargs: Dict[str, Any]) -> None:
        self.data = data
        self.attributes = kwargs
        self.ordering_key = ordering_key

    def __repr__(self) -> str:
        return str(self.to_repr())

    def to_repr(self) -> Dict[str, Any]:
        msg = {
            'data': encode(self.data).decode('utf-8'),
            'attributes': self.attributes,
        }
        if self.ordering_key:
            msg['orderingKey'] = self.ordering_key
        return msg
