

import time

import parts.api as api
import parts.glb as glb
from parts.core.states import LoadState, FileStyle
from parts.pnode import part
from SCons.Debug import logInstanceCreation

from . import base


class All(base.Base):  # task_master type
    '''
    Load all items. This is the main fallback, case of some odd error in another loader.
    This is the basic default the SCons does, which is to load everything
    '''

    def __init__(self, pmanager):
        if __debug__:
            logInstanceCreation(self)
        self.pmgr = pmanager
        self._section_from_cache = set()  # all the section we need to load from cache
        self._parts_to_read = set()  # all the parts we have to readin

    def next_task(self):
        t = self.__tasks[self.__i]
        if t is not None:
            self.__i += 1
        return t

    def stop(self):
        self.__stopped = True
        self.__i = -1

    @property
    def Stopped(self):
        return self.__stopped

    def cleanup(self):
        pass

    def _has_tasks(self):
        return self.__tasks != []

    def DefineTasksList(self):

        for v in list(self.pmgr.parts.values()):
            self.__tasks.append(load_parts_task(v, self.pmgr, self))

    def __call__(self):

        # get all the root parts we have defined
        parts_to_load = list(self.pmgr.parts.values())
        # sort them so they load in the order they are defined
        parts_to_load.sort(key=lambda x: x._order_value)

        total = len(parts_to_load) * 1.0
        cnt = 0
        # in case of a fallback we really want to make sure
        # all known parts are loaded from file. We need to set
        # that state, so any promotions forms of cache to file
        # happen correctly
        t1 = time.time()
        
        # we want to read all the known part files
        
        for pobj in parts_to_load:
            # have the part manager read the given part
            self.pmgr.LoadPart(pobj)
            api.output.console_msg("Loading {0:.2%} \033[K".format(cnt / total, cnt, total))
            cnt += 1
        num_parts = len(self.pmgr.parts)
        tt = time.time() - t1
        if num_parts:
            api.output.verbose_msgf(['loading', 'load_stats'],
                                    "Loaded {0} Parts\n Total time:{1} sec\n Time per part:{2}", num_parts, tt, tt / num_parts)
        api.output.print_msg("Loaded {0} Parts".format(num_parts,))

        # then we want to see based on our target which sections we want to process
        # given this is an all loader we load all sections

        # we need to know what sections are defined

        # Given we have some .. we want to start loading these sections


        for ID, pobj in self.pmgr.parts.items():
            if pobj.Format == FileStyle.CLASSIC:
                # this is a classic format
                # do basic mappings
                pobj._map_exports()
                pobj._setup_sdk()
                pobj._map_targets()


        # we are loading everything..so we don't want to exit early
        return False
