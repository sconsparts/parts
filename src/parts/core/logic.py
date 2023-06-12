# various enums for different logic flows

import enum

import parts.api as api

class VersionLogic(enum.Enum):
    Default = enum.auto() # if there is no value set.. use this value
    Verify = enum.auto() # check that the version passed in matches the value that is set
    StrictVerify = enum.auto() # same as verify but if version not defined errors out
    Force = enum.auto() # override the version value with this value.

api.register.add_global_object("VersionLogic", VersionLogic)