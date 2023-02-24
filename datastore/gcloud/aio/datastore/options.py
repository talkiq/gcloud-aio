from typing import Any
from typing import Dict
from typing import Optional


class ReadWrite:

    def __init__(self, previous_transaction: str):
        self.previous_transaction = previous_transaction

    def to_repr(self) -> Dict[str, str]:
        return {'previousTransaction': self.previous_transaction}


class TransactionOptions:
    def __init__(
            self,
            read_write: Optional[ReadWrite] = None,
            read_only: Any = None):
        self.read_write = read_write
        self.read_only = read_only  # Type not documented

    def to_repr(self) -> Dict[str, Any]:
        d = {}
        if self.read_write:
            d['readWrite'] = self.read_write.to_repr()

        if self.read_only is not None:
            d['readOnly'] = self.read_only

        return d
