
import abc

class UIHost(object):
    """description of class"""

#class C io streams
    @abc.abstractmethod
    def WriteStdOut(self,msg):
        pass

    @abc.abstractmethod
    def WriteStdErr(self,msg):
        pass

# our virtual streams
    @abc.abstractmethod
    def WriteMessage(self,msg):
        pass

    @abc.abstractmethod
    def WriteWarning(self,msg,stack=None):
        pass

    @abc.abstractmethod
    def WriteError(self,msg,stack=None):
        pass

    @abc.abstractmethod
    def WriteDebug(self,catagory,stream):
        '''
        prints a debug message
        catagorty - is the type of verbose message
        msg - is the message to print
        The host may or may not be given all trace messages
        by the engine. The catagory is not added to the message.
        The host can use this value help orginize messages, it is suggested
        that a given message is clearly formatted with the catagory type.
        '''
        pass

    @abc.abstractmethod
    def WriteVerbose(self,catagory,msg):
        '''
        prints a verbose message
        catagorty - is the type of verbose message
        msg - is the message to print
        The host may or may not be given all verbose messages
        by the engine. The catagory is not added to the message.
        The host can use this value help orginize messages, it is suggested
        that a given message is clearly formatted with the catagory type. 
        '''
        pass

    @abc.abstractmethod
    def WriteProgress(self,task,msg=None,progress=None,completed=False):
        '''
        task - string telling the current activity we are doing
        status - string telling the current state of the task
        progress - is a value between 0 and 1, -1 means unknown
        completed - tell us to stop displaying the progress

        Will(/might) extend latter with:
        id - an ID that distinguishes each progress bar from the others.
        parentid - tell the parent task to this progress. ( allow formatting improvments to show relationships)
        time_left - a value to tell us an ETA in some time value

        '''
        pass

    @abc.abstractproperty
    def DebugCatagories(self):
        return []

    @abc.abstractproperty
    def VerboseCatagories(self):
        return []





