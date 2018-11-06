
from __future__ import absolute_import, division, print_function


from . import task


class task_master(object):
    ''' This is a taskmaster that is customized for vcs processing

    Someday SCons will formalize this code, that day we will have something to subclass form.
    Till then this is very dependent on SCons.. the names of the function have to be called this
    '''

    def __init__(self):
        self.__i = 0
        self.__tasks = []
        self.__stopped = False
        self.__return_code = 0

    def check_vcs_output(self, vcsobj):
        '''
        This function checks to see if the checkout path is unique

        The reason for this is that most VCS tools don't allow more than one
        check outs or updates to the same place at the same time.
        This function is not part of the task functions.
        '''
        for i in self.__tasks:
            if vcsobj.CheckOutDir == i.Vcs.CheckOutDir:
                return False
        return True

    def append(self, x):
        if x is None:
            self.__tasks.append(None)
        else:
            if self.check_vcs_output(x):
                self.__tasks.append(task.task(x, self))

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
