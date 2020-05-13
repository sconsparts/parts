

import fnmatch

import parts.api as api
import parts.metatag as metatag
from SCons.Debug import logInstanceCreation


class hasFileExtension:

    def __init__(self, extlist):
        if __debug__:
            logInstanceCreation(self)
        self.extlist = extlist

    def __call__(self, node):
        for i in self.extlist:
            if fnmatch.fnmatchcase(str(node), i):
                return True
        return False


class HasPackageCatagory:

    def __init__(self, catagory):
        if __debug__:
            logInstanceCreation(self)
        self.catagory = catagory

    def __call__(self, node):
        return metatag.MetaTagValue(node, 'category', 'package') == self.catagory


api.register.add_global_object('hasFileExtension', hasFileExtension)
api.register.add_global_object('HasPackageCatagory', HasPackageCatagory)
