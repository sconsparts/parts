


from SCons.Debug import logInstanceCreation


class stored_info(object):
    """description of class"""
    __slots__ = []

    def __init__(self, *args, **kw):
        if __debug__:
            logInstanceCreation(self)

# vim: set et ts=4 sw=4 ai ft=python :
