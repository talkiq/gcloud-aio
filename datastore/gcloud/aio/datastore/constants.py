import datetime
import enum


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
    datetime.datetime: TypeName.TIMESTAMP,
    float: TypeName.DOUBLE,
    int: TypeName.INTEGER,
    str: TypeName.STRING,
    type(False): TypeName.BOOLEAN,
    type(None): TypeName.NULL,
}

FORMATTERS = {
    TypeName.TIMESTAMP: lambda d: d.strftime('%Y-%m-%dT%H:%S:%M.%f000Z'),
}
