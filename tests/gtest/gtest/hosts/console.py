
import sys
import linecache

import interfaces
import gtest.common as common

from optparse import OptionGroup

class ConsoleHost(interfaces.UIHost):
    """description of class"""
    def __init__(self, parser):
        defaults = OptionGroup(parser, 'Console options', 'Arguments unique to console')
        defaults.add_option("--show-color", action='store_true', dest='show_color',
                            help="Show colored output")
        defaults.add_option("--disable-color", dest='show_color', action='store_false',
                            help="Disable colored output")
        defaults.add_option('-v', "--verbose", dest='verbose', action='append',
                            metavar="category", help="Display all verbose messages or only "
                            "messages of provided categories")
        defaults.add_option("--debug", dest='debug', action='append', metavar="category",
                            help="Display all debug messages or only messages of provided "
                            "categories")
        parser.add_option_group(defaults)

        options, args = parser.parse_args()

        self.__verbose = options.verbose or []
        self.__debug = options.debug or []

#class C io streams

    def WriteStdOut(self,msg):
        sys.__stdout__.write(msg)

    def WriteStdErr(self,msg):
        sys.__stderr__.write(msg)

# our virtual streams

    def WriteMessage(self,msg):
        sys.__stdout__.write(msg)


    def get_contents(self, filename, lineno):
        content=''
        if lineno > 3:
            content += "  {0}".format(linecache.getline(filename, lineno-3))
        if lineno > 2:
            content += "  {0}".format(linecache.getline(filename, lineno-2))
        if lineno > 1:
            content += "  {0}".format(linecache.getline(filename, lineno-1))
        content += "-> {0}".format(linecache.getline(filename, lineno))
        content += "  {0}".format(linecache.getline(filename, lineno+1))
        return content

    def WriteWarning(self,msg,stack=None,show_stack=True):
        if show_stack:
            if stack is not None:
                filename, lineno, routine, content=stack
            else:
                frame=sys._getframe(2)
                filename=frame.f_code.co_filename
                lineno= frame.f_lineno
                routine=frame.f_code.co_name
                content=self.get_contents(filename, lineno)

            msg+=' File: "%s", line: %s, in "%s"\n %s\n' % (filename, lineno, routine,content)
        sys.__stdout__.write("Warning: "+msg)


    def WriteError(self,msg,stack=None,show_stack=True,exit=1):
        if show_stack:
            if stack is not None:
                filename, lineno, routine, content=stack
            else:
                frame=sys._getframe(2)
                filename=frame.f_code.co_filename
                lineno= frame.f_lineno
                routine=frame.f_code.co_name
                content=self.get_contents(filename, lineno)

            msg+=' File: "%s", line: %s, in "%s"\n %s\n' % (filename, lineno, routine,content)

        sys.__stderr__.write("Error: "+msg)

        if exit:
            sys.exit(exit)

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
        sys.__stdout__.write("Debug: [{0}] {1}".format(catagory,msg))


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
        sys.__stdout__.write("Verbose: [{0}] {1}".format(catagory,msg))


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

    @property
    def DebugCatagories(self):
        '''
        returns list of string defining the catagories of debug messages we want to have
        processed by the engine
        '''
        return self.__debug

    @property
    def VerboseCatagories(self):
        '''
        returns list of string defining the catagories of verbose messages we want to have
        processed by the engine
        '''
        return self.__verbose

