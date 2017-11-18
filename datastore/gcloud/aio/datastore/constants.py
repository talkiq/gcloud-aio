import enum


class Mode(enum.Enum):
    UNSPECIFIED = 'MODE_UNSPECIFIED'
    TRANSACTIONAL = 'TRANSACTIONAL'
    NON_TRANSACTIONAL = 'NON_TRANSACTIONAL'


class TypeName(enum.Enum):
    BOOLEAN = 'booleanValue'
    NULL = 'nullValue'
    INTEGER = 'integerValue'
    DOUBLE = 'doubleValue'
    TIMESTAMP = 'timestampValue'
    STRING = 'stringValue'
    BLOB = 'blobValue'


class Operation(enum.Enum):
    INSERT = 'insert'
    UPDATE = 'update'
    UPSERT = 'upsert'
    DELETE = 'delete'
