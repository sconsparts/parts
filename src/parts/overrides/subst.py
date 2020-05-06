# this file overides some object in SCons that are just wrong.
# some of the fixes are getting into SCons, however I have to have
# something for the user of old versions that are still broken



import collections

import SCons.Subst

# do we have an hash for Literial?
if not SCons.Subst.Literal.__hash__:
    def __hash__(self):
        return hash(self.lstr)

    SCons.Subst.Literal.__hash__ = __hash__
