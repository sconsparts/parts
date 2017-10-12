
from parts.tools.Common.ToolSetting import ToolSetting
from parts.tools.Common.ToolInfo import ToolInfo
from parts.tools.Common.Finders import RegFinder, EnvFinder, PathFinder, ScriptFinder
from parts.platform_info import SystemPlatform
import SCons.Util
import SCons.Script

from parts import api
import os

OPTC = ToolSetting('OPTC')


OPTC.Register(
    hosts=[SystemPlatform('any', 'any')],
    targets=[SystemPlatform('any', 'any')],
    info=[ToolInfo(
        version='1.0',
        install_scanner=[
                EnvFinder([
                    'OPTTOOLS'
                ]),
            PathFinder([
                "./opttool"
            ])
        ],
        script=None,
        subst_vars={
            'PATH': '${OPTC.INSTALL_ROOT}/bin'
        },
        shell_vars={
            'PATH':
            '${OPTC.PATH}'
        },
        test_file='optc.py'
    )])


def generate(env):

    # variable for the Builder
    # normally this would just the program (ie env['OPTPY']='opt.py'), but since this example use made up
    # tool and we ant to this work, we expand the path out so the real command of python $OPTPY allows
    # the python program to find the tool py file.
    env['OPTCC'] = '${OPTC.PATH}/${OPTC.TOOL}'
    env['OPTCOM'] = 'python $OPTCC $TARGET $OPT $SOURCES'
    env['SDK_OPT'] = '$SDK_ROOT/opt'
    env['OPT'] = []
    env['INSTALL_OPT'] = '$INSTALL_ROOT/opt'
    # merge Shell values to run tool
    OPTC.MergeShellEnv(env)

    def target_scan(node, env, path):
        return env.File(env.get('OPT', []))

    tscan = env.Scanner(name='opt',
                        function=target_scan)

    opt_builder = env.Builder(action=SCons.Action.Action('$OPTCOM', '$OPTCOMSTR'),
                              suffix='.opt',
                              source_factory=SCons.Node.FS.File,
                              target_factory=SCons.Node.FS.File,
                              target_scanner=tscan
                              )
    env['BUILDERS']['OptFile'] = opt_builder

    return


def exists(env):
    return OPTC.Exists(env)


# going forward this code will get updated to use api namespace calls
# ideally the code will become a generator to prevent Copy paste mistakes to
# implenting what are ideally internal details.
def SdkOpt(env, sources, sub_dir='', create_sdk=True):
    from parts.exportitem import EXPORT_TYPES
    ret = env.SdkItem('$SDK_OPT', sources, sub_dir, '', [(EXPORT_TYPES.PATH_FILE, 'OPT')], create_sdk=create_sdk)
    return ret


def InstallOpt(env, src_files, sub_dir='', no_pkg=False, create_sdk=True, **kw):
    import parts.installs  # will want to hide this in refactor
    installed_files = env.InstallItem('$INSTALL_OPT', src_files,
                                      sub_dir=sub_dir, sdk_dir='$SDK_OPT', no_pkg=no_pkg, create_sdk=create_sdk,
                                      **parts.installs.get_args('OPT', **kw))

    env.MetaTag(installed_files, PACKAGING_TYPE='INSTALL_OPT')
    env.ExportItem('INSTALLOPT', installed_files, create_sdk, True)
    return installed_files

# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment
SConsEnvironment.SdkOpt = SdkOpt
SConsEnvironment.InstallOpt = InstallOpt

# setup some requirements
# note !! Code to is not implemented yet to allow the user to add a item to the "Default" set yet.
# Any items added here has to explictly requested at this time. This will be addressed.
# likewise the ability to have REQ.INSTALLFILES, REQ.SDKFILES need to be addressed still
from parts.api.requirement import requirement, requirement_internal, DefineRequirementSet, REQ
DefineRequirementSet('OPT', [requirement('OPT', public=True, policy=REQ.Policy.ignore, listtype=True)])
DefineRequirementSet('SDKOPT', [requirement_internal('SDKOPT', policy=REQ.Policy.ignore, listtype=True, internal=True)])
DefineRequirementSet('INSTALLOPT', [requirement_internal('INSTALLOPT', policy=REQ.Policy.ignore, listtype=True, internal=True)])
