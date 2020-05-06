


import hashlib

import parts.api as api
import parts.errors as errors
import parts.glb as glb
import parts.policy as policies
import parts.requirement as requirement
from SCons.Debug import logInstanceCreation


class dependent_ref(object):
    """This Class allows us to map a dependancy between two different components
    A dependancy allows certain data items, to be defined by the requirements, to
    be shared between the two environments defining each section
    """
    __slots__ = [
        '__part_ref',
        '__sectionname',
        '__requires',
        '__stackframe',
        '__rsigs',
        '__section',
        '__part',
        '__stored_matches'
    ]

    def __init__(self, part_ref, section, requires):
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

    @property
    def StackFrame(self):
        return self.__stackframe

    @property
    def PartRef(self):
        return self.__part_ref

    @property
    def SectionName(self):
        return self.__sectionname

    @property
    def Requires(self):
        return self.__requires

    @property
    def Part(self):
        if self.__part:
            return self.__part
        else:
            if self.__part_ref.hasUniqueMatch:
                self.__part = self.__part_ref.UniqueMatch
            elif self.__part_ref.hasMatch == False:
                api.output.error_msg(self.NoMatchStr(),stackframe=self.StackFrame)
            elif self.__part_ref.hasAmbiguousMatch:
                api.output.error_msg(self.AmbiguousMatchStr(),stackframe=self.StackFrame)
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
        return self.PartRef.delaysubst(value, policy)

    def str_sig(self):
        return "{}:{}:{}".format(self.__part_ref.str_sig(), self.__sectionname, self.__requires.csig())

# vim: set et ts=4 sw=4 ai ft=python :
