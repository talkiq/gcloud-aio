from typing import Dict
from typing import Optional
from typing import Union


class ReadOnly:
    def to_repr(self) -> Dict[str, str]:
        return {}


class ReadWrite:

    def __init__(self, previous_transaction: Optional[str] = None):
        self.previous_transaction = previous_transaction

    def to_repr(self) -> Dict[str, str]:
        if self.previous_transaction:
            return {'previousTransaction': self.previous_transaction}

        return {}


class TransactionOptions:
    # https://cloud.google.com/datastore/docs/reference/data/rest/v1/TransactionOptions

    def __init__(self, option: Union[ReadWrite, ReadOnly]):
        self.option = option

    def to_repr(self) -> Dict[str, Dict[str, str]]:
        if isinstance(self.option, ReadOnly):
            return {'readOnly': self.option.to_repr()}
        if isinstance(self.option, ReadWrite):
            return {'readWrite': self.option.to_repr()}
        raise ValueError(f'invalid TransactionOptions {self.option}')
