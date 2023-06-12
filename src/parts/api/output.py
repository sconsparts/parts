

from builtins import map

import parts.common as common
import parts.glb as glb
import SCons.Script

# no need to redirect data.. assume it is correct.


def error_msg(*lst, **kw):
    glb.engine.HadError = True
    msg = list(map(str, lst))
    msg = kw.get('sep', ' ').join(msg) + kw.get('end', '\n')
    glb.rpter.part_error(msg, kw.get('stackframe', None), kw.get('show_stack', True),
                         kw.get('exit', True), kw.get('show_prefix', True))


def error_msgf(sfmt, *lst, **kw):
    glb.engine.HadError = True
    msg = sfmt.format(*lst, **kw)
    msg = msg + kw.get('end', '\n')
    glb.rpter.part_error(msg, kw.get('stackframe', None), kw.get('show_stack', True),
                         kw.get('exit', True), kw.get('show_prefix', True))


def warning_msg(*lst, **kw):
    msg = list(map(str, lst))
    msg = kw.get('sep', ' ').join(msg) + kw.get('end', '\n')
    glb.rpter.part_warning(msg, kw.get('print_once', False), kw.get('stackframe', None),
                           kw.get('show_stack', True), kw.get('show_prefix', True))


def warning_msgf(sfmt, *lst, **kw):
    msg = sfmt.format(*lst, **kw)
    msg = msg + kw.get('end', '\n')
    glb.rpter.part_warning(msg, kw.get('print_once', False), kw.get('stackframe', None),
                           kw.get('show_stack', True), kw.get('show_prefix', True))


def print_msg(*lst, **kw):
    glb.rpter.part_message([kw.get('sep', ' ')] + list(lst) + [kw.get('end', '\n')], kw.get('show_prefix', True))


def print_msgf(sfmt, *lst, **kw):
    msg = sfmt.format(*lst, **kw)
    glb.rpter.part_message([kw.get('sep', ' '), msg, kw.get('end', '\n')], kw.get('show_prefix', True))


def _verbose_pre(_func, catagory, *lst, **kw):
    if glb.rpter.isSetup == False:
        try:
            glb.rpter.verbose = SCons.Script.GetOption('verbose')
        except AttributeError:
            glb.rpter.verbose = []
    if glb.rpter.verbose is None:
        glb.rpter.verbose = []
    _func(catagory, *lst, **kw)


def _verbose_msgf(catagory, sfmt, *lst, **kw):
    catagory = common.make_list(catagory)
    catagory.append('all')
    msg = common.dformat(sfmt, *lst, **kw)
    glb.rpter.verbose_msg(catagory, [kw.get('sep', ' '), msg, kw.get('end', '\n')])


def _verbose_msg(catagory, *lst, **kw):
    catagory = common.make_list(catagory)
    catagory.append('all')
    glb.rpter.verbose_msg(catagory, [kw.get('sep', ' ')] + list(lst) + [kw.get('end', '\n')])


verbose_msgf = lambda catagory, *lst, **kw: _verbose_pre(_verbose_msgf, catagory, *lst, **kw)
verbose_msg = lambda catagory, *lst, **kw: _verbose_pre(_verbose_msg, catagory, *lst, **kw)


def _trace_pre(_func, catagory, *lst, **kw):
    if glb.rpter.isSetup == False:
        glb.rpter.trace = SCons.Script.GetOption('trace')
    if not glb.rpter.trace:
        glb.rpter.trace = []
    _func(catagory, *lst, **kw)


def _trace_msgf(catagory, sfmt, *lst, **kw):
    msg = common.dformat(sfmt, *lst, **kw)
    glb.rpter.trace_msg(catagory, [kw.get('sep', ' '), msg, kw.get('end', '\n')])


def _trace_msg(catagory, *lst, **kw):
    glb.rpter.trace_msg(catagory, [kw.get('sep', ' ')] + list(lst) + [kw.get('end', '\n')])


trace_msgf = lambda catagory, *lst, **kw: _trace_pre(_trace_msgf, catagory, *lst, **kw)
trace_msg = lambda catagory, *lst, **kw: _trace_pre(_trace_msg, catagory, *lst, **kw)


def policy_msg(policy, catagory, *lst, **kw):
    from ..core import policy as Policy
    if policy == Policy.ReportingPolicy.ignore:
        return
    elif policy == Policy.ReportingPolicy.message:
        print_msg(*lst, **kw)
    elif policy == Policy.ReportingPolicy.verbose:
        verbose_msg(catagory, *lst, **kw)
    elif policy == Policy.ReportingPolicy.warning:
        warning_msg(*lst, **kw)
    elif policy == Policy.ReportingPolicy.error:
        error_msg(*lst, **kw)


def console_msg(*lst, **kw):
    msg = list(map(str, lst))
    glb.rpter.stdconsole(kw.get('sep', ' ').join(msg) + kw.get('end', '\r'))
