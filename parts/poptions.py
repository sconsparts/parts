from __future__ import absolute_import, division, print_function

import os
import sys
from optparse import OptionValueError

import SCons.Script

import parts.api as api
import parts.color as color
import parts.common as common
import parts.core as core
import parts.glb as glb
import parts.load_module as load_module
import parts.logger as logger
import parts.platform_info as platform_info
import parts.settings as settings

# used to help scripts set defaults when there is no config script
def SetOptionDefault(key, value):
    
    args = sys.argv[1:]

    # special logger logic
    if key == 'LOGGER':
        if not isinstance(glb.rpter.logger, logger.QueueLogger):
            api.output.verbose_msg(['settings'], 'Logger already set -- ignoring')
            pass
        else:
            # clean up
            env = settings.DefaultSettings().Environment()
            directory = env.Dir(env['LOG_ROOT_DIR'])
            tmp = env.subst(value)
            if tmp == 'TEXT_LOGGER':
                tmp = env.subst('$' + value)

            if tmp in opt_true_values:
                mod = load_module.load_module(
                    load_module.get_site_directories('loggers'),
                    'text',
                    'logger')
                log_obj = mod.__dict__.get(value, logger.nil_logger)
            elif tmp in opt_false_values:
                log_obj = logger.nil_logger
            else:
                mod = load_module.load_module(
                    load_module.get_site_directories('loggers'),
                    tmp,
                    'logger')
                log_obj = mod.__dict__.get(tmp, logger.nil_logger)
            #####
            log_obj = log_obj(directory.abspath, env['LOG_FILE_NAME'])
            glb.rpter.reset_logger(log_obj)

    api.output.verbose_msg(['settings'], 'Setting default value of', key, 'to', value)
    try:
        settings.DefaultSettings().vars[key].Default = value
    except KeyError:
        settings.DefaultSettings().vars[key] = value


def opt_file(option, opt, value, parser, var, argstr):
    if os.path.exists(value):
        parser.values.__dict__[var] = os.path.abspath(value)
    else:
        raise OptionValueError("Error: %s %s was not found was not found on disk" % (argstr, value))


def opt_target(option, opt, value, parser):

    tmp = platform_info.target_convert(value, error=False)
    if tmp is None:
        raise OptionValueError(
            "Error:  %s is not a valid --target_platform value\nValue must be in form of <Plaform>-<Architecture>" % value)

    parser.values.target_platform = tmp


def opt_chain(option, opt, value, parser):
    tmp = value.split(',')
    lst = []
    for i in tmp:
        lst.append(i.split('_'))
    parser.values.tool_chain = lst


def opt_list(option, opt, value, parser, var):
    parser.values.__dict__[var] = value.split(',')


opt_true_values = set(['y', 'yes', 'true', 't', '1', 'on', 'all'])
opt_false_values = set(['n', 'no', 'false', 'f', '0', 'off', 'none'])


def opt_bool(option, opt, value, parser, var, negate=False):
    if negate:
        TrueValue = False
    else:
        TrueValue = True
    if value is None:
        parser.values.__dict__[var] = TrueValue
        return
    tmp = value.lower()
    if tmp in opt_true_values:
        parser.values.__dict__[var] = TrueValue
    elif tmp in opt_false_values:
        parser.values.__dict__[var] = not TrueValue
    else:
        raise OptionValueError('Invalid value for boolean option "%s" value "%s"\n Valid options are %s' %
                               (var.replace('-', '_'), value, opt_true_values | opt_false_values))


def opt_bool_enum(option, opt, value, parser, var, enum, negate=False):
    if value is None:
        parser.values.__dict__[var] = True
        return
    tmp = value.lower()
    if tmp in opt_true_values:
        parser.values.__dict__[var] = True
    elif tmp in opt_false_values:
        parser.values.__dict__[var] = False
    elif tmp in enum:
        parser.values.__dict__[var] = tmp
    else:
        raise OptionValueError('Invalid value for option "%s" value "%s"\n Valid options are %s' %
                               (var.replace('-', '_'), value, set(enum) | opt_true_values | opt_false_values))


def opt_update(option, opt, value, parser):
    if value is None:
        parser.values.update = True
        return
    tmp = value.split(',')
    if len(tmp) > 1:
        parser.values.update = tmp
        return
    tmp2 = tmp[0].lower()

    if tmp2 in opt_true_values:
        parser.values.update = True
    elif tmp2 in opt_false_values:
        parser.values.update = False
    elif tmp2 in ['auto']:
        parser.values.update = 'auto'
    else:
        parser.values.update = tmp


def opt_color(option, opt, value, parser):
    if value is None:
        value = 'true'
    tmp = value.lower()
    colors = False
    if tmp in opt_false_values:
        colors = None
    elif tmp in set(['full', 'default', 'darkbg', 'y', 'yes', 'true', 't', '1', 'on']):
        colors = {
            'console': color.ConsoleColor(color.BrightMagenta),
            'stdout': color.ConsoleColor(color.Dim),
            'stderr': color.ConsoleColor(color.BrightRed),
            'stdwrn': color.ConsoleColor(color.BrightYellow),
            'stdmsg': color.ConsoleColor(color.Bright),
            'stdverbose': color.ConsoleColor(color.BrightAqua),
            'stdtrace': color.ConsoleColor(color.BrightBlue),
        }
    elif tmp in ['simple']:
        colors = {
            'console': color.ConsoleColor(color.Bright),
            'stdout': color.ConsoleColor(),
            'stderr': color.ConsoleColor(color.BrightRed),
            'stdwrn': color.ConsoleColor(color.BrightYellow),
            'stdmsg': color.ConsoleColor(),
            'stdverbose': color.ConsoleColor(color.BrightAqua),
            'stdtrace': color.ConsoleColor(color.BrightBlue),
        }

    else:
        tmp = value.split(',')
        colors = {
            'console': color.ConsoleColor(color.BrightMagenta),
            'stdout': color.ConsoleColor(color.Dim),
            'stderr': color.ConsoleColor(color.BrightRed),
            'stdwrn': color.ConsoleColor(color.BrightYellow),
            'stdmsg': color.ConsoleColor(color.Bright),
            'stdverbose': color.ConsoleColor(color.BrightAqua),
            'stdtrace': color.ConsoleColor(color.BrightBlue),
        }
        for t in tmp:
            # stuff like "o=blue,e=green"
            try:
                # need better lgic to validate arguments.. but this will do for now
                k, v = t.split('=')
            except:
                raise OptionValueError('Error: Invalid stream type to set color for: "%s" valid stream types are:\n\
 console, con, tty\n\
 stdout, out, o\n\
 stderr, error, err, e\n\
 stdwrn, warning, wrn, w\n\
 stdmsg, message, msg, m\n\
 stdverbose, verbose, ver, v\n\
 stdtrace, trace, t' % t)
            k = k.lower()
            if k in ['c', 'con', 'tty', 'console']:
                colors['console'] = color.parse_color(v)
            elif k in ['o', 'out', 'stdout']:
                colors['stdout'] = color.parse_color(v)
            elif k in ['e', 'err', 'error', 'stderr']:
                colors['stderr'] = color.parse_color(v)
            elif k in ['w', 'wrn', 'warning', 'stdwrn']:
                colors['stdwrn'] = color.parse_color(v)
            elif k in ['m', 'msg', 'message', 'stdmsg']:
                colors['stdmsg'] = color.parse_color(v)
            elif k in ['v', 'ver', 'verbose', 'stdverbose']:
                colors['stdverbose'] = color.parse_color(v)
            elif k in ['t', 'trace', 'stdtrace']:
                colors['stdtrace'] = color.parse_color(v)
            else:
                raise OptionValueError('Error: Invalid stream type to set color for: "%s" valid stream types are:\n\
 console, con, tty, c\n\
 stdout, out, o\n\
 stderr, error, err, e\n\
 stdwrn, warning, wrn, w\n\
 stdmsg, message, msg, m\n\
 stdverbose, verbose, ver, v\n\
 stdtrace, trace, t' % k)
    if colors == False:
        raise OptionValueError("Invalid value for setting color: %s" % value)

    parser.values.use_color = colors


def opt_logging(option, opt, value, parser):
    if value is None:
        value = 'text'
    tmp = value.lower()
    try:
        if tmp in opt_true_values:
            def_logger = 'text'
            mod = load_module.load_module(
                load_module.get_site_directories('loggers'),
                def_logger,
                'logger')
            parser.values.logger = mod.__dict__.get(def_logger, logger.nil_logger)
        elif tmp in opt_false_values:
            parser.values.logger = logger.nil_logger
        else:
            mod = load_module.load_module(
                load_module.get_site_directories('loggers'),
                value,
                'logger')
            parser.values.logger = mod.__dict__.get(value, logger.nil_logger)
    except ImportError:
        raise OptionValueError('No logger called "%s" was found' % value)


SCons.Script.AddOption("--use-parts-site",
                       dest='use_part_site',
                       default=None,
                       nargs=1,
                       type='string',
                       action='store',
                       # metavar='DIR',
                       help='User provided part-site path. Overides all default location.')

SCons.Script.AddOption("--disable-global-parts-site",
                       dest='global_part_site',
                       default=False,
                       action="store_false",
                       help='Disable Parts from using the part-site location in the system or user areas.')

SCons.Script.AddOption("--use-env",
                       dest='use_env',
                       default=False,
                       action="store_true",
                       help='Force use of shell environment. Overrides normal tools path setup')

SCons.Script.AddOption("--verbose",
                       dest='verbose',
                       default=[],
                       callback=lambda option, opt, value, parser: opt_list(
                           option, opt, value if value is not None else 'all', parser, 'verbose'),
                       nargs="?", type='string',
                       action='callback',
                       help='Control the level of detailed verbose information printed')

SCons.Script.AddOption("--trace",
                       dest='trace',
                       default=[],
                       callback=lambda option, opt, value, parser: opt_list(option, opt, value, parser, 'trace'),
                       nargs=1, type='string',
                       action='callback',
                       help='Control the level of trace information printed')

SCons.Script.AddOption("--log",
                       dest='logger',
                       default=logger.QueueLogger,
                       nargs='?',
                       callback=opt_logging,
                       type='string',
                       action='callback',
                       help='True to use default logger, else name of logger to use')

SCons.Script.AddOption("--build-config", "--buildconfig", "--bldcfg", "--bcfg", "--cfg",
                       dest='build_config',
                       default=None,
                       nargs=1, type='string',
                       action='store',
                       help='The configuration to use')

SCons.Script.AddOption("--tool-chain", "--toolchain", "--tc",
                       dest='tool_chain',
                       default=None,
                       nargs=1,
                       callback=opt_chain,
                       type='string',
                       action='callback',
                       help='Tool chains to use for build')


SCons.Script.AddOption("--mode",
                       dest='mode',
                       default=None,
                       nargs=1,
                       callback=lambda option, opt, value, parser: opt_list(option, opt, value, parser, 'mode'),
                       type='string',
                       action='callback',
                       help='Values used to control different build mode for a given part')

SCons.Script.AddOption("--disable-parts-cache",
                       dest="parts_cache",
                       default=True,
                       action="store_true",
                       help='Disable Parts data cache from being used')

SCons.Script.AddOption("--load-logic", "--ll",
                       dest='load_logic',
                       default='default',
                       nargs=1,
                       type='choice',
                       choices=['all', 'target', 'min', 'unsafe', 'default'],
                       action='store',
                       help='Tells Parts what logic to use when loading files. Options are "all", "target", "min", "unsafe", "default"')

SCons.Script.AddOption("--disable-color",
                       dest='use_color',
                       callback=lambda option, opt, value, parser: opt_color(option, opt, False, parser),
                       type='string',
                       action='callback',
                       help='Controls if console color support is used')

SCons.Script.AddOption("--enable-color", "--use-color", "--color",
                       dest='use_color',
                       nargs="?",
                       default={
                           'console': color.ConsoleColor(color.BrightMagenta),
                           'stdout': color.ConsoleColor(color.Dim),
                           'stderr': color.ConsoleColor(color.BrightRed),
                           'stdwrn': color.ConsoleColor(color.BrightYellow),
                           'stdmsg': color.ConsoleColor(color.Bright),
                           'stdverbose': color.ConsoleColor(color.BrightAqua),
                           'stdtrace': color.ConsoleColor(color.BrightBlue),
                           'defaults': True
                       },
                       callback=opt_color,
                       type='string',
                       action='callback',
                       help='Controls if console color support is used')

SCons.Script.AddOption("--ccopy", '--ccopy-logic', '--copy-logic',
                       dest='ccopy_logic',
                       default=None,
                       nargs=1,
                       # callback=opt_ccopy,
                       type='choice',
                       choices=['hard-soft-copy', 'soft-hard-copy', 'soft-copy', 'hard-copy', 'copy'],
                       action='store',
                       help='Control how Parts copy logic will work must be hard-soft-copy,soft-hard-copy, soft-copy, hard-copy, copy')

SCons.Script.AddOption('--vcs-update', '--update',
                       dest='update',
                       default='auto',
                       nargs='?',
                       callback=opt_update,
                       type='string',
                       action='callback',
                       help='Controls if Parts should update the Vcs object, and which Parts to update.')

SCons.Script.AddOption("--enable-vcs-clean", "--vcs-clean",
                       dest='vcs_clean',
                       default=False,
                       nargs='?',
                       callback=lambda option, opt, value, parser: opt_bool(option, opt, value, parser, 'vcs_clean'),
                       type='string',
                       action='callback',
                       help='Controls if VCS update should ensure a clean, unmodifed, factory defaults update.')

SCons.Script.AddOption("--enable-vcs-retry", "--vcs-retry",
                       dest='vcs_retry',
                       default=False,
                       nargs='?',
                       callback=lambda option, opt, value, parser: opt_bool(option, opt, value, parser, 'vcs_retry'),
                       type='string',
                       action='callback',
                       help='Controls if an failure with a VCS update or checkout is allow to retry the update by removing the existing code')

SCons.Script.AddOption("--vcs-logic",
                       dest='vcs_logic',
                       default='check',
                       nargs=1,
                       type='choice',
                       choices=['none', 'exists', 'check', 'force'],
                       action='store',
                       help='Control logic of how Parts will automatically do vcs up date checks. Values must be none, exists, check, force')

SCons.Script.AddOption("--vcs-job", '--vcsj', '--vj',
                       dest='vcs_jobs',
                       default=0,
                       nargs=1,
                       type='int',
                       action='store',
                       help='Level of concurrent VCS checkouts/updates that can happen at once. Defaults to -j value if not set')

SCons.Script.AddOption("--disable-section-suppression",
                       dest="section_suppression",
                       default=True,
                       action="store_false",
                       help='Disable process suppression of any sections defined in a Part via the SUPPRESS_SECTION variable')

SCons.Script.AddOption("--per-thread-logging",
                       dest="thread_logging_path",
                       default=None,
                       action="store",
                       help='Enable per-thread task logging to the specified directory')

# move to end as work around to a bug in SCons
SCons.Script.AddOption("--cfg-file", "--config-file",
                       dest='cfg_file',
                       default=os.path.abspath('parts.cfg'),
                       nargs=1,
                       callback=lambda option, opt, value, parser: opt_file(option, opt, value, parser, 'cfg_file', "config file:"),
                       type='string',
                       action='callback',
                       help='Configuration file used to store common settings')

# policy values
SCons.Script.AddOption("--vcs-policy",
                       dest='vcs_policy',
                       default='message-update',
                       nargs=1,
                       type='choice',
                       choices=['warning', 'error', 'message-update', 'warning-update',
                                'update', 'checkout-warning', 'checkout-error'],
                       action='store',
                       help='Policy in how Parts should react if the automatic vcs check find that it is out of date.\
 The policy values can be warning, error, message_update, warning-update, update, checkout-warning, checkout-error')


def post_option_setup():
    ''' These options need to be setup in a delayed way
    '''
    SCons.Script.AddOption("--target", "--target-platform",
                           dest='target_platform',
                           default=None,
                           nargs=1,
                           callback=opt_target,
                           type='string',
                           action='callback',
                           help='Sets the default TARGET_PLATFORM use for cross builds')


SCons.Script.SConsOptions.SConsValues.settable.extend(
    [
        'vcs_logic',
        'vcs_policy',
        'vcs_jobs',
        'vcs_retry',
        'vcs_clean',
        'update',
        'ccopy_logic',
        'use_color',
        'show_progress',
        'mode',
        'build_config',
        'tool_chain'
    ])

api.register.add_global_object('SetOptionDefault', SetOptionDefault)
api.register.add_list_variable('SUPPRESS_SECTION', [], 'Tells Parts to not define any sections of this type')
