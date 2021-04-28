
import parts.api as api
from parts.errors import GetPartStackFrameInfo


class Context:
    '''
    This class is used for the general context object that might be defined by a sections and passed to a given phase
    This object define some basic logic to make error handling easy for common cases in which the user mistyped a meathod
    and to force hide certain items from the user.
    '''

    __slots__ = (
        '_locked',
    )

    def __init__(self):
        self._locked = False

    def _lock(self):
        self._locked = True

    def _unlock(self):
        self._locked = False

    def __getattr__(self, name):
        try:
            return self.__getattribute__(name)
        except AttributeError:
            options = []
            for key in self.__dict__.keys():
                if key in name or name in key:
                    options.append(key)
            if options:
                api.output.error_msg(f"{name} is not a member, Did you mean {' or '.join(options)}",stack=GetPartStackFrameInfo())
            else:
                api.output.error_msg(f"{name} is not a member, Possible values are: {', '.join(self.__dict__.keys())}",stack=GetPartStackFrameInfo())

    def __setattr__(self, name, val):
        if name in self.__slots__:
            super().__setattr__(name,val)
        else:
            try:
                lock = self.__getattribute__("_locked")
            except AttributeError:
                lock = False

            if lock and name not in self.__dict__:
                options = []
                for key in self.__dict__.keys():
                    if key in name or name in key:
                        options.append(key)
                if options:
                    api.output.error_msg(f"{name} is not a member, Did you mean {' or '.join(options)}",stack=GetPartStackFrameInfo())
                else:
                    api.output.error_msg(f"{name} is not a member, Possible values are: {', '.join(self.__dict__.keys())}",stack=GetPartStackFrameInfo())
            else:
                self.__dict__[name] = val