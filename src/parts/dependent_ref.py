
import hashlib

import parts.api as api
import parts.errors as errors
import parts.glb as glb
import parts.core.policy as policies
import parts.part_ref as part_ref
import parts.requirement as requirement
from parts.pnode.nilpart import NilPart
from SCons.Debug import logInstanceCreation


class dependent_ref:
    """This Class allows us to map a dependency between two different components
    A dependency allows certain data items, to be defined by the requirements, to
    be shared between the two environments defining each section
    """
    __slots__ = [
        '__part_ref', # the PartRef object
        '__sectionname', # the sections we want to match in the dependent part
        '__requires', # stuff we want to map
        '__stackframe', # debug stack frame info
        '__rsigs', # requirement signature | May not be needed any more
        '__section', # the section we match
        '__part', # The part we match
        '__stored_matches',
        '__classically_mapped', # this was mapped via the "classic" mapper logic
        '__optional' # if this depend optional? ie we can skip it if not found
    ]

    def __init__(self, part_ref: part_ref.PartRef, section, requires, optional=False):
        if __debug__:
            logInstanceCreation(self)

        errors.SetPartStackFrameInfo()
        self.__part_ref = part_ref
        self.__sectionname = section

        self.__requires = requirement.REQ() | requires
        self.__stackframe = errors.GetPartStackFrameInfo()
        errors.ResetPartStackFrameInfo()

        self.__rsigs = None
        self.__section = None
        self.__part = None
        self.__stored_matches = None
        self.__optional = optional
        self.__classically_mapped = False

    @property
    def StackFrame(self):
        return self.__stackframe

    @property
    def PartRef(self):
        return self.__part_ref

    @property
    def SectionName(self) -> str:
        return self.__sectionname

    @property
    def Requires(self):
        return self.__requires

    @property
    def isOptional(self) -> bool:
        return self.__optional

    @property
    def isClassicallyMapped(self):
        return self.__classically_mapped

    @isClassicallyMapped.setter
    def isClassicallyMapped(self, val):
        self.__classically_mapped = val

    @property
    def Part(self):
        if self.__part:
            return self.__part
        else:
            if self.__part_ref.hasUniqueMatch:
                self.__part = self.__part_ref.UniqueMatch
            elif not self.__part_ref.hasMatch and not self.__optional:
                api.output.error_msg(self.NoMatchStr(), stackframe=self.StackFrame)
            elif not self.__part_ref.hasMatch and self.__optional:
                # this component is viewed as optional
                api.output.warning_msg(self.NoMatchStr(), stackframe=self.StackFrame, print_once=True)
                self.__part = NilPart()
            elif self.__part_ref.hasAmbiguousMatch:
                api.output.error_msg(self.AmbiguousMatchStr(), stackframe=self.StackFrame)
        return self.__part

    @property
    def StoredMatchingSections(self):

        if self.__stored_matches is None:
            self.__stored_matches = []
            matches = self.__part_ref.StoredMatches
            # try to turn matches in to sections
            for m in matches:
                stored = m.Stored
                if stored:
                    tmp = glb.pnodes.GetPNode(stored.SectionIDs[self.__sectionname])
                    self.__stored_matches.append(tmp)
                else:
                    self.__stored_matches.append(m.Section(self.__sectionname))
        return self.__stored_matches

    @property
    def hasAmbiguousMatch(self):
        return self.__part_ref.hasAmbiguousMatch

    @property
    def hasMatch(self):
        return self.__part_ref.hasMatch

    @property
    def hasStoredMatch(self):
        return self.__part_ref.hasStoredMatch

    @property
    def hasUniqueMatch(self):
        return self.__part_ref.hasUniqueMatch

    @property
    def hasStoredUniqueMatch(self):
        return self.__part_ref.hasStoredUniqueMatch

    @property
    def UniqueMatch(self):
        return self.__part_ref.UniqueMatch

    @property
    def StoredUniqueMatch(self):
        return self.__part_ref.StoredUniqueMatch

    @property
    def StoredUniqueMatchSection(self):
        return self.StoredMatchingSections[0]

    # clean up the below functions... so we only have one case
    @property
    def Section(self):
        if self.__section:
            return self.__section
        else:
            self.__section = self.Part.Section(self.SectionName)
        return self.__section

    def NoMatchStr(self):
        return "Failed to map dependency because:\n {0}".format(self.__part_ref.NoMatchStr())

    def AmbiguousMatchStr(self):
        return "Failed to map dependency because:\n {0}".format(self.__part_ref.AmbiguousMatchStr())

    def RSigs(self):
        if self.__rsigs is None:
            self._gen_rsigs()
        return self.__rsigs

    def _gen_rsigs(self):
        md5_rsig = hashlib.md5()
        rsigs = {}
        esigs = self.Section.ESigs()
        for req in self.__requires:
            try:
                esig = esigs[req.key]
                md5_rsig.update(esig)
                rsigs[req.key] = esig
            except KeyError:
                pass

        # self.__rsig=md5_rsig.hexdigest()
        self.__rsigs = rsigs

    # this should be a safe API for users
    def DelaySubst(self, value, policy=policies.REQPolicy.warning):
        return self.PartRef.delaysubst(value, self.SectionName , policy)

    def str_sig(self):
        return "{}:{}:{}".format(self.__part_ref.str_sig(), self.__sectionname, self.__requires.csig())

# vim: set et ts=4 sw=4 ai ft=python :
