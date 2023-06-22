

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


class HasPackageCategory:

    def __init__(self, category):
        if __debug__:
            logInstanceCreation(self)
        self.category = category

    def __call__(self, node):
        return metatag.MetaTagValue(node, 'category', 'package') == self.category

class HasPackageCatagory(HasPackageCategory):
    def __call__(self, node):
        api.output.warning_msg("[HasPackageCatagory] is deprecated, please use [HasPackageCategory]")
        return super.__call__(self, node)

api.register.add_global_object('hasFileExtension', hasFileExtension)
api.register.add_global_object('HasPackageCatagory', HasPackageCatagory) # deprecated and emits a warning message on use
api.register.add_global_object('HasPackageCategory', HasPackageCategory)
