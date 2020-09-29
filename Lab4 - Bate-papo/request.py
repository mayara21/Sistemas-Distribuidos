from enum import Enum

class Request(Enum):
    ENTER_CHAT = 'enter'
    GET_USER = 'get'
    LIST_USERS = 'list'
    VALIDATE_CONNECTION = 'validate'
    CHECK_USER_CONNECTION = 'check'