import enum
from datetime import datetime as dt


class CompositeFilterOperator(enum.Enum):
    AND = 'AND'
    UNSPECIFIED = 'OPERATOR_UNSPECIFIED'


class Consistency(enum.Enum):
    EVENTUAL = 'EVENTUAL'
    STRONG = 'STRONG'
    UNSPECIFIED = 'READ_CONSISTENCY_UNSPECIFIED'


class Direction(enum.Enum):
    ASCENDING = 'ASCENDING'
    DESCENDING = 'DESCENDING'
    UNSPECIFIED = 'DIRECTION_UNSPECIFIED'


class Mode(enum.Enum):
    NON_TRANSACTIONAL = 'NON_TRANSACTIONAL'
    TRANSACTIONAL = 'TRANSACTIONAL'
    UNSPECIFIED = 'MODE_UNSPECIFIED'


class MoreResultsType(enum.Enum):
    MORE_RESULTS_AFTER_CURSOR = 'MORE_RESULTS_AFTER_CURSOR'
    MORE_RESULTS_AFTER_LIMIT = 'MORE_RESULTS_AFTER_LIMIT'
    NO_MORE_RESULTS = 'NO_MORE_RESULTS'
    NOT_FINISHED = 'NOT_FINISHED'
    UNSPECIFIED = 'MORE_RESULTS_TYPE_UNSPECIFIED'


class Operation(enum.Enum):
    DELETE = 'delete'
    INSERT = 'insert'
    UPDATE = 'update'
    UPSERT = 'upsert'


class PropertyFilterOperator(enum.Enum):
    EQUAL = 'EQUAL'
    GREATER_THAN = 'GREATER_THAN'
    GREATER_THAN_OR_EQUAL = 'GREATER_THAN_OR_EQUAL'
    HAS_ANCESTOR = 'HAS_ANCESTOR'
    LESS_THAN = 'LESS_THAN'
    LESS_THAN_OR_EQUAL = 'LESS_THAN_OR_EQUAL'
    UNSPECIFIED = 'OPERATOR_UNSPECIFIED'


class ResultType(enum.Enum):
    FULL = 'FULL'
    KEY_ONLY = 'KEY_ONLY'
    PROJECTION = 'PROJECTION'
    UNSPECIFIED = 'RESULT_TYPE_UNSPECIFIED'


class TypeName(enum.Enum):
    BLOB = 'blobValue'
    BOOLEAN = 'booleanValue'
    DOUBLE = 'doubleValue'
    INTEGER = 'integerValue'
    KEY = 'keyValue'
    NULL = 'nullValue'
    STRING = 'stringValue'
    TIMESTAMP = 'timestampValue'


# TODO: add types for geoPointValue and arrayValue
TYPES = {
    bool: TypeName.BOOLEAN,
    bytes: TypeName.BLOB,
    dt: TypeName.TIMESTAMP,
    float: TypeName.DOUBLE,
    int: TypeName.INTEGER,
    str: TypeName.STRING,
    type(None): TypeName.NULL,
}
