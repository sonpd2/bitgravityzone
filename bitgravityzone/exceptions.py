from enum import IntEnum
import json


class GravityZoneException(Exception):
    ...


class ClientError(GravityZoneException):
    def __init__(self, *args, endpoint, method, params, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = endpoint
        self.method = method
        self.params = params


class AuthenticationError(ClientError):
    ...


class AuthorizationError(ClientError):
    ...

class MethodNotFound(ClientError):
    ...

class InvalidParams(ClientError):
    ...


class JsonRpcError(IntEnum):
    PARSE_ERROR      = -32700
    INVALID_REQUEST  = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS   = -32602
    SERVER_ERROR     = -32000


def raise_error(request, response):
    err = response.json()['error']
    body = json.loads(request.content.decode())

    info = {
        'endpoint': request.url.path.split('/')[-1],
        'method': body['method'],
        'params': body['params'],
    }

    msg = err['data']['details']
    exc = None

    if response.status_code == 401:
        exc = AuthenticationError
    elif response.status_code == 403:
        exc = AuthorizationError
    elif err['code'] == JsonRpcError.METHOD_NOT_FOUND:
        exc = MethodNotFound
    elif err['code'] == JsonRpcError.INVALID_PARAMS:
        exc = InvalidParams

    if exc:
        raise exc(msg, **info) from None
    # TODO
    else:
        raise GravityZoneException(msg)
