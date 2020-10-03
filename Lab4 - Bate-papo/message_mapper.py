import struct
from user import User
from method import Method
from status import Status

ENCODING = 'utf-8'

class Message_Mapper():

    # Connect to chat Mapping

    @staticmethod
    def pack_connect_request(name: str, ip: str, port: int):
        method_bytes: bytes = _pack_method(Method.ENTER_CHAT.value)

        name_bytes: bytes = _pack_name(name)
        ip_bytes: bytes = _pack_ip(ip)
        port_bytes: bytes = _pack_port(port)

        return (method_bytes + name_bytes + ip_bytes + port_bytes)


    @staticmethod
    def unpack_connect_request(message: bytearray):
        user_name = _unpack_name(message)    
        user_ip = _unpack_ip(message[16:20])
        user_port = _unpack_port(message[20:])

        return User(user_name, user_ip, user_port)

    
    # Get User Mapping

    @staticmethod
    def pack_get_user_request(name: str):
        method_bytes: bytes = _pack_method(Method.GET_USER.value)
        names_bytes: bytes = _pack_name(name)

        return method_bytes + names_bytes


    @staticmethod
    def unpack_get_user_request(message: bytearray):
        return _unpack_name(message)
    

    @staticmethod
    def pack_get_user_response(name: str, ip: str, port: int):
        method = Method.GET_USER.value
        header = Message_Mapper.pack_ok_response(method)

        bytes_name: bytes = _pack_name(name)
        bytes_ip: bytes = _pack_ip(ip)
        bytes_port: bytes = _pack_port(port)
        
        return header + bytes_name + bytes_ip + bytes_port

    @staticmethod
    def unpack_get_user_response(message: bytearray):
        user_name = _unpack_name(message)    
        user_ip = _unpack_ip(message[16:20])
        user_port = _unpack_port(message[20:])

        return User(user_name, user_ip, user_port)


    # Check User Mapping

    @staticmethod
    def pack_check_user_request(name: str):
        method_bytes: bytes = _pack_method(Method.CHECK_USER_CONNECTION.value)
        name_bytes: bytes = _pack_name(name)

        return method_bytes + name_bytes

    @staticmethod
    def unpack_check_user_request(message: bytearray):
        return _unpack_name(message)


    # List Mapping
    
    @staticmethod
    def pack_get_list_request():
        return _pack_method(Method.LIST_USERS.value)


    @staticmethod
    def pack_get_list_response(simplified_list):        
        header = Message_Mapper.pack_ok_response(Method.LIST_USERS.value)
        
        list_size = len(simplified_list)
        list_size_bytes: bytes = struct.pack('=H', list_size)
        names_bytes: bytes = b''

        for i in range(list_size):
            names_bytes += struct.pack('=16s', simplified_list[i].encode(ENCODING))

        return header + list_size_bytes + names_bytes

    @staticmethod
    def unpack_get_list_response(message: bytearray):
        list_size = int(struct.unpack('=H', message[:2])[0])
        user_list = []

        for i in range(list_size):
            j = 2 + i*16
            user = str(struct.unpack('=16s', message[j: j + 16])[0], encoding=ENCODING).strip('\x00')
            user_list.append(user)

        return user_list



    # P2P Messages Mapping

    @staticmethod
    def pack_message_send(name: str, message: str):
        name_bytes: bytes = _pack_name(name)
        message_size = len(message)
        message_size_bytes: bytes = struct.pack('=H', message_size)

        message_bytes = struct.pack('=' + str(message_size) + 's', message.encode(ENCODING))

        return name_bytes + message_size_bytes + message_bytes


    @staticmethod
    def unpack_message_receive(message: bytearray):
        name = _unpack_name(message)
        message_size = int(struct.unpack('=H', message[16:18])[0])

        message = str(struct.unpack('=' + str(message_size) + 's', message[18:])[0], encoding=ENCODING)

        return (name, message)



    # User ID Message Mapping

    @staticmethod
    def pack_user_id_on_connect_message(name: str):
        bytes_method: bytes = _pack_method(Method.GET_USER_ID.value)
        bytes_name: bytes = _pack_name(name)

        return bytes_method + bytes_name


    @staticmethod
    def unpack_user_id_on_connect_message(message: bytearray):
        return _unpack_name(message)



    # OK and Error Mapping

    @staticmethod
    def pack_ok_response(method):
        method_bytes: bytes = _pack_method(method)
        status_bytes: bytes = struct.pack('=B', Status.OK.value)

        return method_bytes + status_bytes


    @staticmethod
    def pack_error_response(method, message):
        method_bytes: bytes = _pack_method(method)
        status_bytes: bytes = struct.pack('=B', Status.ERROR.value)
        error_message: bytes = struct.pack('=256s', message.encode(ENCODING))

        return method_bytes + status_bytes + error_message


    @staticmethod
    def unpack_error_response(message):
        return str(struct.unpack('=256s', message[:256])[0], encoding=ENCODING).strip('\x00')


    # Method Mapping

    @staticmethod
    def pack_method(method):
        return _pack_method(method)


    @staticmethod
    def unpack_method(message):
        return _unpack_method(message)

    
    # Status Mapping

    @staticmethod
    def unpack_status(message):
        return _unpack_status(message)

        

# Basic packing

def _pack_status(status: int):
    return struct.pack('=B', status)

def _pack_method(method: str):
    return struct.pack('=8s', method.encode(ENCODING))

def _pack_name(name: str):
    return struct.pack('=16s', name.encode(ENCODING))


def _pack_ip(ip: str):
    ip_bytes: bytes = b''
    ip_parts: list = ip.split(".")
    for part in ip_parts:
        ip_bytes += struct.pack('=B', int(part))

    return ip_bytes

def _pack_port(port: int):
    return struct.pack('=H', port)


# Basic unpacking

def _unpack_method(message: bytearray):
    return str(struct.unpack('=8s', message[:8])[0], encoding=ENCODING).strip('\x00')

def _unpack_status(message):
    return int(struct.unpack('=B', message[:1])[0])

def _unpack_name(message):
    return str(struct.unpack('=16s', message[:16])[0], encoding=ENCODING).strip('\x00')


def _unpack_ip(message):
    user_ip: str = ''

    for i in range(3):
        user_ip += str(struct.unpack('=B', message[i:i + 1])[0]) + '.'
        
    user_ip += str(struct.unpack('=B', message[3:4])[0])

    return user_ip


def _unpack_port(message):
    return int((struct.unpack('=H', message[:2])[0]))