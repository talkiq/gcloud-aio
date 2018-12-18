import enum
from datetime import datetime as dt


class Consistency(enum.Enum):
    EVENTUAL = 'EVENTUAL'
    READ_CONSISTENCY_UNSPECIFIED = 'READ_CONSISTENCY_UNSPECIFIED'
    STRONG = 'STRONG'


class Mode(enum.Enum):
    NON_TRANSACTIONAL = 'NON_TRANSACTIONAL'
    TRANSACTIONAL = 'TRANSACTIONAL'
    UNSPECIFIED = 'MODE_UNSPECIFIED'


class Operation(enum.Enum):
    DELETE = 'delete'
    INSERT = 'insert'
    UPDATE = 'update'
    UPSERT = 'upsert'


class TypeName(enum.Enum):
    BLOB = 'blobValue'
    BOOLEAN = 'booleanValue'
    DOUBLE = 'doubleValue'
    INTEGER = 'integerValue'
    NULL = 'nullValue'
    STRING = 'stringValue'
    TIMESTAMP = 'timestampValue'


# TODO: support more than just scalars
TYPES = {
    bytes: TypeName.BLOB,
    dt: TypeName.TIMESTAMP,
    float: TypeName.DOUBLE,
    int: TypeName.INTEGER,
    str: TypeName.STRING,
    type(False): TypeName.BOOLEAN,
    type(None): TypeName.NULL,
}

FORMATTERS = {
    TypeName.TIMESTAMP: lambda d: d.strftime('%Y-%m-%dT%H:%S:%M.%f000Z'),
}

UNFORMATTERS = {
    TypeName.DOUBLE: lambda s: float(s),
    TypeName.INTEGER: lambda s: int(s),
    TypeName.TIMESTAMP: lambda s: dt.strptime(s, '%Y-%m-%dT%H:%S:%M.%f000Z'),
}
