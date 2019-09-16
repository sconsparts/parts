from __future__ import absolute_import, division, print_function

import os
import re
import sys
from builtins import map

import parts.api as api
import parts.common as common
import parts.console as console
import parts.core as core
import parts.errors as errors
import parts.glb as glb
import parts.logger as logger
import parts.policy as Policy
import SCons.Errors
import SCons.Script
# not ideal...
import SCons.Script.Main
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

if 'stacktrace' in (SCons.Script.GetOption('debug') or []):
    class PartRuntimeError(SCons.Errors.StopError):
        pass
else:
    class PartRuntimeError(SCons.Errors.UserError):
        pass


class streamer(object):

    def __init__(self, outfunc):
        self.outfunc = outfunc

    def write(self, str):
        return self.outfunc(msg=str)

    def flush(self):
        pass


warning_tests = [
    re.compile(r'(\A|\s)warning?\s?(([?!: ])|(\.\s))\D', re.IGNORECASE).search
]

error_tests = [
    re.compile(r'(\A|\s)error?\s?(([?!: ])|(\.\s))\D', re.IGNORECASE).search,
    re.compile('fail$', re.IGNORECASE).match
]

message_tests = [
    re.compile(r'(scons?\s?:)', re.IGNORECASE).search,
    re.compile(r'(parts?\s?:)', re.IGNORECASE).search,
    re.compile(r'(Install file?\s?:)').search,
]

DEFAULT_STREAM = 0
OUT_STREAM = 1
MESSAGE_STREAM = 2
WARNING_STREAM = 3
ERROR_STREAM = 4


def remap(s, org_stream):
    global last_type
    if s != "":
        if is_warning(s):
            return WARNING_STREAM
        if is_error(s):
            return ERROR_STREAM
        if is_message(s) and org_stream == OUT_STREAM:
            return MESSAGE_STREAM
    return DEFAULT_STREAM


def is_warning(str):
    for test in warning_tests:
        if test(str):
            return True
    return False


def is_error(str):
    for test in error_tests:
        if test(str):
            return True
    return False


def is_message(str):
    for test in message_tests:
        if test(str):
            return True
    return False


class reporter(object):

    def __init__(self):

        # so we can process any text that is being outputted by some other means
        self.trace = []

        # remap the streams.  (may want to delay even more...)
        self.console = console.Console()
        sys.stdout = streamer(self.stdout)
        sys.stderr = streamer(self.stderr)

        # setup the rest of the stuff
        self.logger = logger.QueueLogger()
        self.already_printed = set()
        self.silent = False
        self.verbose = []
        self.__is_setup = False

    def Setup(self, logger, silent, verbose, trace, use_color):

        self.silent = silent
        if use_color == False or use_color is None:
            self.console.ProcessColor = False
        else:
            self.console.ProcessColor = True
            self.console.Color = use_color['console']
            self.console.Output.Color = use_color['stdout']
            self.console.Error.Color = use_color['stderr']
            self.console.Warning.Color = use_color['stdwrn']
            self.console.Message.Color = use_color['stdmsg']
            self.console.Trace.Color = use_color['stdtrace']
            self.console.Verbose.Color = use_color['stdverbose']

        self.trace = trace
        if self.trace == []:
            api.output.trace_msg = _empty_msg
            api.output.trace_msgf = _empty_msg
        else:
            api.output.trace_msg = api.output._trace_msg
            api.output.trace_msgf = api.output._trace_msgf

        self.verbose = verbose
        if self.verbose == []:
            api.output.verbose_msg = _empty_msg
            api.output.verbose_msgf = _empty_msg
        else:
            api.output.verbose_msg = api.output._verbose_msg
            api.output.verbose_msgf = api.output._verbose_msgf

        self.logger = logger
        self.__is_setup = True

    def ShutDown(self):
        self.logger.ShutDown()
        self.console.ShutDown()

    def reset_logger(self, obj):
        '''
        reset the log data when our logger is a QueueLogger to the new
        logger object by adding data in QueueLogger to new object
        '''
        if isinstance(self.logger, logger.QueueLogger) and not isinstance(obj, logger.QueueLogger):
            for t, msg in self.logger.queue:
                if t == console.Console.out_stream:
                    obj.logout(msg)
                elif t == console.Console.error_stream:
                    obj.logerr(msg)
                elif t == console.Console.warning_stream:
                    obj.logwrn(msg)
                elif t == console.Console.message_stream:
                    obj.logmsg(msg)
                elif t == console.Console.trace_stream:
                    obj.logtrace(msg)
                elif t == console.Console.verbose_stream:
                    obj.logverbose(msg)
            self.logger = obj

    @property
    def isSetup(self):
        return self.__is_setup

    def part_warning(self, msg, print_once=False, stackframe=None, show_stack=True):

        s = "Parts: Warning: " + msg
        if show_stack:
            if stackframe is not None:
                filename, lineno, routine, content = stackframe
            else:
                filename, lineno, routine, content = errors.GetPartStackFrameInfo()
            s += ' File "%s", line %s, in "%s"\n %s\n' % (filename, lineno, routine, content)

        if print_once == True:
            if hash(s) not in self.already_printed:
                self.already_printed.add(hash(s))
            else:
                return
        self.console.Warning.write(s)
        self.logger.logwrn(s)

    def part_error(self, msg, stackframe=None, show_stack=True, exit=True):

        s = "Parts: Error!: " + msg
        if show_stack:
            if stackframe is not None:
                filename, lineno, routine, content = stackframe
            else:
                filename, lineno, routine, content = errors.GetPartStackFrameInfo()
            s += ' File: "%s", line: %s, in "%s"\n %s\n' % (filename, lineno, routine, content)

        self.console.Error.write(s)
        self.logger.logerr(s)
        if exit:
            raise PartRuntimeError("Unrecoverable Error!")

    def part_message(self, msg_lst, show_prefix):
        if self.silent == False:
            msg = list(map(str, msg_lst[1:-1]))
            msg = msg_lst[0].join(msg) + msg_lst[-1]
            if show_prefix:
                s = "Parts: " + msg
            else:
                s = msg
            self.stdmsg(s, False)

    def verbose_msg(self, catagory, msg_lst):
        tmp = common.make_list(catagory)
        for c in tmp:
            if c.lower() in self.verbose:
                msg = list(map(str, msg_lst[1:-1]))
                msg = msg_lst[0].join(msg) + msg_lst[-1]
                s = 'Verbose: [%s] %s' % (tmp[0], msg)
                self.stdverbose(s)
                break

    def trace_msg(self, catagory, msg_lst):
        tmp = common.make_list(catagory)
        for c in tmp:
            if c.lower() in self.trace:
                msg = list(map(str, msg_lst[1:-1]))
                msg = msg_lst[0].join(msg) + msg_lst[-1]
                s = 'Trace: [%s] %s' % (tmp[0], msg)
                self.stdtrace(s)

    def user_warning(self, env, msg, print_once=False, stackframe=None, show_stack=True):
        if env.get("PART_NAME") is None:
            s = "User Warning: " + msg
        else:
            s = 'User Warning from Part Named "%s": %s' % (env.PartName(), msg)
        if show_stack:
            if stackframe is not None:
                filename, lineno, routine, content = stackframe
            else:
                filename, lineno, routine, content = errors.GetPartStackFrameInfo()
            s += ' File: "%s", line: %s, in "%s"\n %s\n' % (filename, lineno, routine, content)

        if print_once == True:
            if hash(s) not in self.already_printed:
                self.already_printed.add(hash(s))
            else:
                return
        self.console.Warning.write(s)
        self.logger.logwrn(s)

    def user_error(self, env, msg, stackframe=None, show_stack=True, exit=True):

        if env.get("PART_NAME") is None:
            s = "User Error: " + msg
        else:
            s = 'User Error from Part Named "%s": %s' % (env.PartName(), msg)
        if show_stack:
            if stackframe is not None:
                filename, lineno, routine, content = stackframe
            else:
                filename, lineno, routine, content = errors.GetPartStackFrameInfo()
            s += ' File: "%s", line: %s, in "%s"\n %s\n' % (filename, lineno, routine, content)

        self.console.Error.write(s)
        self.logger.logerr(s)
        if exit:
            raise PartRuntimeError("Unrecoverable Error!")

    def user_message(self, env, msg):
        if self.silent == False:
            if env.get("PART_NAME") is None:
                s = "Message: " + msg
            else:
                s = 'Message from Part "%s": %s' % (env.PartName(), msg)
            self.stdmsg(s, False)

    def remapped(self, msg, org_stream):
        remap_type = remap(msg, org_stream)
        if remap_type == DEFAULT_STREAM:
            return False
        if remap_type == ERROR_STREAM:
            self.stderr(msg, False)
        elif remap_type == WARNING_STREAM:
            self.stdwrn(msg, False)
        elif remap_type == MESSAGE_STREAM:
            self.stdmsg(msg, False)

        return True

    def stdout(self, msg, remap=True):
        '''This function gets all redirected stdout text from random print calls'''
        if remap == True:
            if self.remapped(msg, OUT_STREAM) == False:
                self.console.Output.write(msg)
                self.logger.logout(msg)
        else:
            self.console.write(msg)
            self.logger.logout(msg)
        return len(msg)

    def stderr(self, msg, remap=True):
        '''This will gets any stderr text in scons via a print>>stderr usage'''
        #print>> sys.__stderr__, "Error message"
        if remap == True:
            if self.remapped(msg, ERROR_STREAM) == False:
                self.console.Error.write(msg)
                self.logger.logerr(msg)
        else:
            self.console.Error.write(msg)
            self.logger.logerr(msg)
        return len(msg)

    def stdwrn(self, msg, remap=True):
        '''Unlike stdout and stderr, stdwrn doesn't really exist.. but we use
        this to pass text that is in a warning state from with in parts'''
        if remap == True:
            if self.remapped(msg, WARNING_STREAM) == False:
                self.console.Warning.write(msg)
                self.logger.logwrn(msg)
        else:
            self.console.Warning.write(msg)
            self.logger.logwrn(msg)
        return len(msg)

    def stdmsg(self, msg, remap=True):
        '''Unlike stdout and stderr, stdmsg doesn't really exist.. but we use
        this to pass text that is a message form the system parts or SCons'''
        if remap == True:
            if self.remapped(msg, MESSAGE_STREAM) == False:
                self.console.Message.write(msg)
                self.logger.logmsg(msg)
        else:
            self.console.Message.write(msg)
            self.logger.logmsg(msg)
        return len(msg)

    def stdtrace(self, msg, remap=True):
        '''Unlike stdout and stderr, stdtrace doesn't really exist.. '''
        self.console.Trace.write(msg)
        self.logger.logtrace(msg)
        return len(msg)

    def stdverbose(self, msg, remap=True):
        '''Unlike stdout and stderr, stdverbose doesn't really exist.. '''
        self.console.Verbose.write(msg)
        self.logger.logverbose(msg)
        return len(msg)

    def stdconsole(self, msg, remap=True):
        '''writes to the Console directly... nice for progress effects'''
        self.console.write(msg)
        return len(msg)


def _empty_msg(catagory, *lst, **kw):
    pass


# user level functions
# global version (for Sconstruct file)
def user_report_error(*lst, **kw):
    msg = list(map(str, lst))
    msg = kw.get('sep', ' ').join(msg) + kw.get('end', '\n')
    glb.rpter.user_error(SCons.Script.DefaultEnvironment(), msg, kw.get('stackframe', None), kw.get('show_stack', False))


def user_report_warning(*lst, **kw):
    msg = list(map(str, lst))
    msg = kw.get('sep', ' ').join(msg) + kw.get('end', '\n')
    glb.rpter.user_warning(SCons.Script.DefaultEnvironment(), msg, kw.get(
        'print_once', False), kw.get('stackframe', None), kw.get('show_stack', False))


def user_print_msg(*lst, **kw):
    msg = list(map(str, lst))
    glb.rpter.user_message(SCons.Script.DefaultEnvironment(), kw.get('sep', ' ').join(msg) + kw.get('end', '\n'))


def user_verbose(catagory, *lst, **kw):
    catagory = common.make_list(catagory)
    catagory.append('all')
    catagory.append('user')
    if glb.rpter.isSetup == False:
        glb.rpter.verbose = SCons.Script.GetOption('verbose')
        if glb.rpter.verbose is None:
            glb.rpter.verbose = []
    glb.rpter.verbose_msg(catagory, [kw.get('sep', ' ')] + list(lst) + [kw.get('end', '\n')])

# env version


def user_report_error_env(env, *lst, **kw):
    msg = list(map(str, lst))
    msg = kw.get('sep', ' ').join(msg) + kw.get('end', '\n')
    glb.rpter.user_error(env, msg, kw.get('stackframe', None), kw.get('show_stack', True))


def user_report_warning_env(env, *lst, **kw):
    msg = list(map(str, lst))
    msg = kw.get('sep', ' ').join(msg) + kw.get('end', '\n')
    glb.rpter.user_warning(env, msg, kw.get('print_once', False), kw.get('stackframe', None), kw.get('show_stack', False))


def user_print_msg_env(env, *lst, **kw):
    msg = list(map(str, lst))
    glb.rpter.user_message(env, kw.get('sep', ' ').join(msg) + kw.get('end', '\n'))


def user_verbose_env(env, catagory, *lst, **kw):
    catagory = common.make_list(catagory)
    catagory.append('all')
    catagory.append('user')
    if glb.rpter.isSetup == False:
        glb.rpter.verbose = SCons.Script.GetOption('verbose')
        if glb.rpter.verbose is None:
            glb.rpter.verbose = []
    glb.rpter.verbose_msg(catagory, [kw.get('sep', ' ')] + list(lst) + [kw.get('end', '\n')])


api.register.add_bool_variable('STREAM_WARNING_AS_ERROR', False, 'Controls is warning based messages are treated as errors')

api.register.add_global_object('PrintError', user_report_error)
api.register.add_global_object('PrintWarning', user_report_warning)
api.register.add_global_object('PrintMessage', user_print_msg)
api.register.add_global_object('VerboseMessage', user_verbose)


api.register.add_global_parts_object('PrintError', user_report_error)
api.register.add_global_parts_object('PrintWarning', user_report_warning)
api.register.add_global_parts_object('PrintMessage', user_print_msg)
api.register.add_global_parts_object('VerboseMessage', user_verbose)

# adding logic to Scons Enviroment object
SConsEnvironment.PrintError = user_report_error_env
SConsEnvironment.PrintWarning = user_report_warning_env
SConsEnvironment.PrintMessage = user_print_msg_env
SConsEnvironment.VerboseMessage = user_verbose_env
