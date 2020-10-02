from enum import Enum

class Request(Enum):
    ENTER_CHAT = 'ENTER'
    GET_USER = 'GET'
    LIST_USERS = 'LIST'
    VALIDATE_CONNECTION = 'VALIDATE'
    CHECK_USER_CONNECTION = 'CHECK'