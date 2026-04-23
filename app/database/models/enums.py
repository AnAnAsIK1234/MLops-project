from enum import Enum


class ModelSource(str, Enum):
    API = "api"
    LOCAL = "local"


class JobStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class TransactionType(str, Enum):
    TOP_UP = "top_up"
    DEBIT = "debit"


class RequestSource(str, Enum):
    FORM = "form"
    FILE = "file"