from enum import Enum

class Method(Enum):
    ENTER_CHAT = 'ENTER'
    GET_USER = 'GET'
    LIST_USERS = 'LIST'
    VALIDATE_CONNECTION = 'VALIDATE'
    CHECK_USER_CONNECTION = 'CHECK'
    GET_USER_ID = 'USER_ID'