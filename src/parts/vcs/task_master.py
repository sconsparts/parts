


from . import update_task
from . import mirror_task


class task_master:
    ''' This is a taskmaster that is customized for vcs processing

    Someday SCons will formalize this code, that day we will have something to subclass form.
    Till then this is very dependent on SCons.. the names of the function have to be called this
    '''

    def __init__(self):
        self.__i = 0
        self.__tasks = []
        self.__stopped = False
        self.__return_code = 0

    def has_checkout_path(self, vcsobj) -> bool:
        '''
        This function checks to see if the checkout path is unique

        The reason for this is that most VCS tools don't allow more than one
        check outs or updates to the same place at the same time.
        This function is not part of the task functions.
        '''
        for i in self.__tasks:
            if isinstance(i,update_task.task) and vcsobj.CheckOutDir == i.Vcs.CheckOutDir:
                return True
        return False

    def has_mirror_path(self, vcsobj) -> bool:
        '''
        This function checks to see if the mirror path is unique.

        Only need to mirror the items once

        '''
        for i in self.__tasks:
            if isinstance(i,mirror_task.task) and vcsobj.MirrorPath == i.Vcs.MirrorPath:
                return True
        return False

    def append(self, x, mirror=False):
        if x is None:
            self.__tasks.append(None)
        elif mirror:
            if not self.has_mirror_path(x):
                self.__tasks.append(mirror_task.task(x, self))
        elif not self.has_checkout_path(x):
                self.__tasks.append(update_task.task(x, self))

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

    @property
    def ReturnCode(self):
        return self.__return_code

    @ReturnCode.setter
    def ReturnCode(self, value):
        self.__return_code = value

    def cleanup(self):
        pass

    def _has_tasks(self):
        return self.__tasks != []
