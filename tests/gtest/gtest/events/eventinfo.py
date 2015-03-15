
class eventinfo(object):
    def __init__(self):
        pass

class StartingInfo(eventinfo):
    def __init__(self):
        pass

class StartedInfo(eventinfo):
    def __init__(self):
        pass

class RunningInfo(eventinfo):
    def __init__(self):
        pass

    @property
    def TotalRunTime(self):
        return 0
    
class FinishedInfo(eventinfo):
    def __init__(self,returncode,runtime,streamwriter):
        self.__returncode=returncode
        self.__runtime=runtime
        self.__all_file=streamwriter.FullFile
        self.__stdout_file=streamwriter.StdOutFile
        self.__stderr_file=streamwriter.StdErrFile
        self.__message_file=streamwriter.MessageFile
        self.__warning_file=streamwriter.WarningFile
        self.__error_file=streamwriter.ErrorFile
        self.__verbose_file=streamwriter.VerboseFile
        self.__debug_file=streamwriter.DebugFile

    @property
    def TotalRunTime(self):
        return self.__runtime

    @property
    def ReturnCode(self):
        return self.__returncode

    @property
    def AllFile(self):
        return self.__all_file
    @property
    def StdOutFile(self):
        return self.__stdout_file
    @property
    def StdErrFile(self):
        return self.__stderr_file
    @property
    def MessageFile(self):
        return self.__message_file
    @property
    def WarningFile(self):
        return self.__warning_file
    @property
    def ErrorFile(self):
        return self.__error_file
    @property
    def VerboseFile(self):
        return self.__verbose_file
    @property
    def DebugFile(self):
        return self.__debug_file