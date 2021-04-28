

import sys

import parts.api as api
import SCons.Errors
from parts.reporter import PartRuntimeError as PartRuntimeError


class task:
    '''
    This is a simple class that does nothing more than have the Scm object update
    itself on disk. This is used to for parallel checkouts/updates.
    Someday SCons will formalize this code, that day we will have something to subclass form.
    Till then this is very dependent on SCons.. the names of the function have to be called this
    '''

    def __init__(self, scm, taskmaster):
        self.__scm = scm
        self.__failed = False
        self.__taskmaster = taskmaster
        self.__orginial_part_log_name = None

    @property
    def Scm(self):
        ''' Allow access to the SCM object as this is a SCM task'''
        return self.__scm

    def prepare(self):
        ''' this is called before the task starts.

        Set up any logic or to figure out if anything should execute.
        '''
        self.___orginial_part_log_name = self.__scm._env["LOG_PART_FILE_NAME"]
        self.__scm._env["LOG_PART_FILE_NAME"] = "${SCM_CACHE_LOG_PART_FILE_NAME}"

    def needs_execute(self):
        ''' reports if anything should execute'''
        return 1

    def execute(self):
        ''' this is what we call to do the checkout'''
        try:
            try:
                if self.__scm.UpdateMirrorOnDisk():
                    self.failed()
            except PartRuntimeError:
                self.failed()
        except Exception:
            import traceback
            import io
            traceback.print_exc()
            raise

    def exception_set(self, exception=None):
        self.__failed = True

    def failed(self):
        api.output.error_msgf("Scm Cache task failed for Part {0}", self.__scm._env.get('ALIAS'), show_stack=False, exit=False)
        self.__taskmaster.stop()

    def executed(self):
        ''' this gets called when everything execute() correctly'''
        pass

    def postprocess(self):
        ''' this always gets called after the task ran, failed or not'''
        self.__scm._env["LOG_PART_FILE_NAME"] = self.___orginial_part_log_name
        self.__scm.ProcessResult(not self.__failed)
        pass


# this is the logic file for per part logging we want to use when we are getting source
api.register.add_variable('SCM_CACHE_LOG_PART_FILE_NAME', 'SCM-mirror-${PART_ALIAS}.log', '')
