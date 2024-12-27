from enum import IntEnum
from typing import TypedDict


class PackageType(IntEnum):
    SECURITY_VIRTUAL_APPLIANCE = 3
    ENDPOINT_SECURITY_TOOLS    = 4


class AccountRole(IntEnum):
    COMPANY_ADMIN = 1
    NETWORK_ADMIN = 2
    REPORTER      = 3
    PARTNER       = 4
    CUSTOM        = 5


class Package(TypedDict):
    id:   str
    name: str
    type: PackageType
