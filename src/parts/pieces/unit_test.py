

import os
import stat
import sys

import parts.api as api
import parts.api.output as output
import parts.common as common
import parts.core.util as util
import parts.errors as errors
import parts.functors as functors
import parts.glb as glb
import parts.node_helpers as node_helpers
import parts.parts as parts
import parts.pattern as pattern
import parts.pnode as pnode
import SCons.Script
from parts.requirement import REQ
from parts.target_type import target_type
# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# map unit testing stuff.. clean up depends..

###########################################
# unit test script file writer
###########################################


def unit_test_script_bf_str(target=None, source=None, env=None):
    return "PARTS: Writing unit test launch scripts"


def unit_test_script_bfe(target, source, env):
    # get target file
    tf = target[0]
    # make new name
    target += [env.File(tf.name + '.cmd', tf.dir)]
    return (target, source)


def unit_test_script_bf(target, source, env):
    target_py, target_cmd = target
    with open(target_py.path, 'wb') as f:

        cmd = env.subst("$UNIT_TEST_RUN_COMMAND")
        if cmd.startswith("#"):
            cmd = cmd[1:]
        api.output.verbose_msgf(["unit_test.script_generation","unit_test"],'Generating script with command of:\n {}',cmd)
        # UNIT_TEST_ENV may be a dict or a list of (key, value) tuples
        command_env = {}
        for (key, value) in dict(env.get('UNIT_TEST_ENV', {})).items():
            command_env[key] = env.subst(value)

        command = '''#! /usr/bin/env python

import os
import sys
import subprocess

curr_path = os.path.split(os.path.abspath(sys.argv[0]))[0]
os.chdir(curr_path)
env = os.environ
env.update(''' + str(command_env) + ''')
env['UNIT_TEST_DIR'] = curr_path
cmd = r"''' + cmd + '''"
if len(sys.argv) > 1:
    cmd = cmd+" "+' '.join(sys.argv[1:])
else:
    cmd = cmd
print(cmd)
proc = subprocess.Popen (cmd, env=env, shell=True)
proc.wait()
sys.stdout.flush()
sys.stderr.flush()
sys.exit(proc.returncode)

'''
        f.write(command.encode())
    with open(target_cmd.path, 'wb') as f:
        f.write(("@pushd %~dp0\r\n@python " + target_py.name +
                 " %*\r\nset ERROR_LEVEL=%ERRORLEVEL%\r\n@popd\r\nexit %ERROR_LEVEL%").encode())
    st = os.stat(target_py.path)
    os.chmod(target_py.path, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IEXEC)
    st = os.stat(target_cmd.path)
    os.chmod(target_cmd.path, stat.S_IMODE(st[stat.ST_MODE]) | stat.S_IEXEC)


def unit_test(env, target, source, command_args=None, data_src=None, src_dir='.', make_pdb=True,
              depends=None, builder="Program", builder_kw={}, **kw):

    # to help with user errors
    errors.SetPartStackFrameInfo()
    
    builder_kw=builder_kw.copy()
    if ("utest::" in env["SUPPRESS_SECTION"] or
            "utest" in env["SUPPRESS_SECTION"]) and \
            SCons.Script.GetOption('section_suppression'):
        api.output.verbose_msgf("warning",
                                'Skipping the processing of Part section "utest" in Part {0}',
                                env.PartName())
        return []
    skip_run_test = False
    if ("run_utest::" in env["SUPPRESS_SECTION"] or
            "run_utest" in env["SUPPRESS_SECTION"]) and \
            SCons.Script.GetOption('section_suppression') \
            or (env['HOST_OS'] != env['TARGET_OS']):
        api.output.verbose_msgf("warning", ('Skipping the processing of Part section'
                                            ' "run_utest" of section "utest" in Part {0}'), env.PartName())
        skip_run_test = True

    # get Part object of Part defining the utest call
    parent_obj = glb.engine._part_manager._from_env(env)
    # Create a section object ( should get existing section if it already exists
    sec = glb.pnodes.Create(pnode.section.utest_section, parent_obj, env=env.Clone(**kw))
    # add section to Part container
    parent_obj._AddSection("utest", sec)
    # Set the "current defining section" to the utest section
    # and save current section to be reset at end of function
    curr_sec = parent_obj.DefiningSection
    try:
        parent_obj.DefiningSection = sec

        # tweak Environment
        sec.Env['UNIT_TEST_TARGET'] = target

        # setup the varible with paths
        curr_path = env.AbsDir('.')
        rel_src_dir = common.relpath(env.AbsDir(src_dir), curr_path)
        if src_dir != '.':
            src_dir = common.relpath(
                env.Dir(os.path.join(curr_path, src_dir)).srcnode().abspath,
                env.Dir('.').abspath)
        else:
            src_dir = curr_path

        src_dir = os.path.abspath(os.path.join(curr_path, rel_src_dir))

        scons_dir_node = env.Dir('#')
        build_dir_leaf = sec.Env['UNIT_TEST_TARGET']
        build_dir = sec.Env.subst("{0}/{1}".format('$BUILD_DIR', build_dir_leaf))
        orig_build_node = env.Dir('$BUILD_DIR')
        orig_build_dir = orig_build_node.path
        rel_build_dir = orig_build_node.Dir(rel_src_dir).path

        # change the build dir
        sec.Env.VariantDir(variant_dir=build_dir, src_dir=src_dir, duplicate=env['duplicate_build'])
        build_dir_node = sec.Env.Dir(build_dir)

        # this is the items outside the src_dir area
        oot_build_dir = sec.Env.subst("{0}/{1}".format(build_dir, 'oot'))
        sec.Env.VariantDir(variant_dir=oot_build_dir, src_dir="#", duplicate=env['duplicate_build'])
        oot_build_dir_node = sec.Env.Dir(oot_build_dir)

        def make_node(fstr, node=None):
            # path is to relative to the src directory            
            if fstr.startswith(rel_src_dir):
                fstr = fstr[len(rel_src_dir) + 1:]
            # abs path to current location of part file calling unit test
            elif fstr.startswith(curr_path):
                fstr = fstr[len(curr_path) + 1:]
            # variant form for original build section of node
            elif fstr.startswith(orig_build_dir):
                if node and (node.srcnode().path == node.path or node.has_builder()):
                    # this is node that is in the build dir
                    # need to return the original object
                    return node
                # this is not best test, but exists allow "legacy" cases
                # to work, however those cases should probally be changed
                # it allows use to refer to node in a test directory
                # as if it was in the directory defining the test
                # however this also deal with source files that are formed
                # with AbsFileNode
                elif node and node.srcnode().exists():
                    # need to make this a node we
                    # can use in the unit test build directory
                    return make_node("#" + node.srcnode().path)
                else:
                    fstr = fstr[len(orig_build_dir) + 1:]
            elif fstr.startswith(rel_build_dir):
                fstr = fstr[len(rel_build_dir) + 1:]
            # start with #
            elif fstr.startswith("#"):
                fnode = sec.Env.File(fstr)
                # is this under the current part directory
                if fnode.is_under(curr_path):
                    fstr = curr_path.rel_path(fnode)
                # is this under the new src directory
                elif fnode.is_under(src_dir):
                    fstr = src_dir.rel_path(fnode)
                # is this under the Scons root
                elif fnode.is_under(scons_dir_node):
                    fstr = scons_dir_node.rel_path(fnode)
                    return oot_build_dir_node.File(fstr)
            return build_dir_node.Entry(fstr)

        # map autodepends stuff
        if depends is None:
            sec.Env.DependsOn([sec.Env.Component(env.PartName(), env.PartVersion(),
                                                 section='build', requires=REQ.DEFAULT(internal=False))])
        else:
            sec.Env.DependsOn(depends)

        # flatten the sources
        source = sec.Env.Flatten(source)

        # process the sources
        # we have to re-path value to map to the new variant directory
        src_files = []
        for f in source:
            if isinstance(f, pattern.Pattern):
                flst = f.files()
                for i in flst:
                    fn = make_node(i)
                    src_files.append(fn)
            elif isinstance(f, SCons.Node.FS.Dir):
                output.warning_msgf("Cannot build directories in unittest()\n Node={0}\n Skipping...", f.ID)
            elif isinstance(f, SCons.Node.FS.File):
                # File node will start with the original build directory
                # or the start with current path ( ie full path to src)
                # or it might be equal to some messed up value based on the build directory
                # caused by the mix of ../ paths
                fn = make_node(f.path, f)
                src_files.append(fn)
            elif isinstance(f, SCons.Node.FS.Entry):
                # Entry (like File) node will start with the original build directory
                # or the start with current path ( ie full path to src)
                # or it might be equal to some messed up value based on the build directory
                # caused by the mix of ../ paths
                fn = make_node(f.path, f)
                src_files.append(fn)
            elif util.isString(f):
                # normalize the path so we get matches on windows and posix based systems
                f = os.path.normpath(f)
                fn = make_node(sec.Env.subst(f))
                src_files.append(fn)
            else:
                api.output.warning_msg("Unknown type in unit_test() in unit_test.py in Part", env.subst('$PART_NAME'))

        # flatten the sources
        data_src = sec.Env.Flatten(data_src or [])

        # process any data files
        out = []
        dest_dir = sec.Env.Dir("$UNIT_TEST_DIR")
        for s in data_src:
            if isinstance(s, pattern.Pattern):
                t, sr = s.target_source(dest_dir)
                out += sec.Env.CCopyAs(target=t, source=sr)
                # print "Pattern type"
            elif isinstance(s, SCons.Node.FS.Dir):
                # get all file in the directory
                # ... add code...
                out += sec.Env.CCopy(target=dest_dir, source=s)
                # print "Dir type"
            elif isinstance(s, SCons.Node.FS.File):
                out += sec.Env.CCopy(target=dest_dir, source=s)
                # print "File type"
            elif isinstance(s, SCons.Node.Node):
                out += sec.Env.CCopy(target=dest_dir, source=s)
            elif util.isString(s):
                f = env.subst(s)
                if f.startswith(rel_src_dir):
                    f = f[len(rel_src_dir) + 1:]
                elif f.startswith(curr_path):
                    f = f[len(curr_path) + 1:]
                f = build_dir_node.File(f)
                out += sec.Env.CCopy(target=dest_dir, source=f)
            else:
                api.output.warning_msg("Unknown type in unit_test() in unit_test.py in Part", env.subst('$PART_NAME'))

        # the current path
        sec.Env.Append(CPPPATH=[src_dir])

        # the option to build with PDB or not
        # might not to do this any more... as the PDB will work correctly on non windows systems
        if make_pdb:
            sec.Env['PDB'] = build_dir + "/" + sec.Env['UNIT_TEST_TARGET_NAME'] + '.pdb'
        elif 'PDB' in sec.Env:
            del sec.Env['PDB']

        # the unit test we want to build
        tmp_bld = getattr(sec.Env, builder)        
        if tmp_bld is None:
            api.output.error_msg("Builder {0} is not found".format(builder))
        api.output.verbose_msgf(['unit_test'],'Using builder "{}"', builder)
        if 'target' not in builder_kw:
            builder_kw['target'] = build_dir + "/" + sec.Env['UNIT_TEST_TARGET_NAME']
        if 'source' not in builder_kw:
            builder_kw['source'] = src_files
        api.output.verbose_msgf(['unit_test'],'calling with args {}', builder_kw)
        ret = tmp_bld(**builder_kw)
        

        # build alias
        build_alias = '${PART_BUILD_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}'
        a = sec.Env.Alias(build_alias)

        tmp = []
        for i in ret:
            if isinstance(i, SCons.Node.FS.File) or isinstance(i, SCons.Node.Node) or util.isString(i):
                if common.is_category_file(sec.Env, 'INSTALL_LIB_PATTERN', i):
                    tmp += sec.Env.CCopy(target='$INSTALL_LIB', source=i)
                else:  # if common.is_category_file(env, 'SDK_BIN_PATTERN', i):
                    tmp += sec.Env.CCopy(target='$INSTALL_BIN', source=i)
        ret = tmp

        # make command args string
        if command_args:
            sec.Env['UTEST_CMDARGS'] = command_args

        # this builder makes the scripts to run the test on
        # the command line with ease
        for k, v in sec.Env.get('UNIT_TEST_ENV', {}).items():
            sec.Env['ENV'][k] = sec.Env.subst(v)
        # in case a python script is being called.. it is the same version of python as we are using
        sec.Env.PrependENVPath('PATH', os.path.split(sys.executable)[0], delete_existing=True)
        scripts_out = sec.Env.__UTEST__(
            build_dir + "/_scripts_/" + sec.Env['UNIT_TEST_SCRIPT_NAME'], [],
            # Need to convert UNIT_TEST_ENV dictionary into a list
            # of (key, value) pairs to make SCons correctly track changes
            # in its contents.
            UNIT_TEST_ENV=list(sec.Env.get('UNIT_TEST_ENV', {}).items())
        )
        scripts_out = sec.Env.CCopy("$UNIT_TEST_DIR", scripts_out)
        # here we map a bunch of aliases
        core_alias = sec.Env.Alias(
            '${BUILD_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::${UNIT_TEST_TARGET}', a + scripts_out + out + ret)
        # map top level run alias... first one maps to build based 'base_alias'
        if not skip_run_test:
            def wrap_exit_code_function(function, env, stackframe):
                '''
                SCons.Action object accepts exitstatfunc argument to be a callable
                with returncode as its only parameter. We want to pass some more arguments
                to our function.
                '''
                return lambda rcode: function(rcode, env=env, stackframe=stackframe)

            core_run_alias_env = sec.Env.Override(
                dict(
                    TIME_OUT=sec.Env.get("RUN_UTEST_TIME_OUT", sec.Env.get('TIME_OUT')),
                    LOG_PART_FILE_NAME='run_utest.{0}.log'.format(ret[0].name)
                )
            )
            core_run_alias = core_run_alias_env.Alias(
                '${RUN_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::${UNIT_TEST_TARGET}',
                core_alias,
                core_run_alias_env.Action(
                    '$UNIT_TEST_RUN_SCRIPT_COMMAND',
                    exitstatfunc=wrap_exit_code_function(
                        core_run_alias_env['RUN_UTEST_EXIT_FUNCTION'], core_run_alias_env, errors.GetPartStackFrameInfo()
                    )
                )
            )
            sec.Env.AlwaysBuild(core_run_alias)

        # utest::alias::palias -> utest::alias::palias::group
        #base_alias = sec.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}', core_alias)
        # print(1,base_alias[0].ID,"->",core_alias[0].ID)
        if not skip_run_test:
            base_run_alias = sec.Env.Alias('${RUN_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}', core_run_alias)
            sec.Env.AlwaysBuild(base_run_alias)

        # utest::alias::palias:: -> utest::alias::palias
        #recurse_alias = sec.Env.Alias('${BUILD_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::', base_alias)
        # print(2,recurse_alias[0].ID,"->",base_alias[0].ID)
        if not skip_run_test:
            recurse_run_alias = sec.Env.Alias('${RUN_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::', base_run_alias)
            sec.Env.AlwaysBuild(recurse_run_alias)

        #talias = common.map_alias_to_root(sec.Part, 'utest', '{0}::${{PART_ALIAS_CONCEPT}}{1}::')

        if not skip_run_test:
            talias_run = common.map_alias_to_root(sec.Part, 'run_utest', '{0}::${{PART_ALIAS_CONCEPT}}{1}::')
            sec.Env.AlwaysBuild(talias_run)

        # Top level
        #sec.Env.Alias('${BUILD_UTEST_CONCEPT}', talias)
        if not skip_run_test:
            r = sec.Env.Alias('${RUN_UTEST_CONCEPT}', talias_run)
            sec.Env.AlwaysBuild(r)
    finally:
        parent_obj.DefiningSection = curr_sec
        errors.ResetPartStackFrameInfo()
    sec.LoadState = glb.load_file
    sec._map_targets()
    
    return ret


def run_utest_return_default(code, env=None, stackframe=None):
    '''
    Callback to be called on unit-test exit.
    @param code: unit-test process exit code.
    @param env: Environment used to define run unit-test Action object.
    @param stackframe: Tuple of (filename, lineno, routine, content).
    '''
    return code


# adding logic to Scons Environment object
SConsEnvironment.UnitTest = unit_test

api.register.add_builder('__UTEST__', SCons.Script.Builder(
    action=SCons.Script.Action(
        unit_test_script_bf,
        unit_test_script_bf_str,
        varlist=[
            'UNIT_TEST_RUN_COMMAND',
            'UNIT_TEST_ENV'
        ]),
    emitter=unit_test_script_bfe,
))

api.register.add_variable('BUILD_UTEST_CONCEPT', 'utest${ALIAS_SEPARATOR}', 'Defines namespace for building a unit test')
api.register.add_variable('RUN_UTEST_CONCEPT', 'run_utest${ALIAS_SEPARATOR}', 'Defines namespace for running a unit test')

api.register.add_variable('UTEST_PREFIX', 'utest-', 'prefix used by UnitTest to prefix alias name')

api.register.add_variable('UTEST_ALL', '$BUILD_UTEST_CONCEPT', 'Alias used to build all defined unit tests')
api.register.add_variable('RUN_UTEST_ALL', '$RUN_UTEST_CONCEPT', 'Alias used to run all defined unit tests')

api.register.add_variable('UNIT_TEST_ROOT', '#_unit_tests', 'Root path used as sandbox for unit test runs')
api.register.add_variable('UNIT_TEST_DIR',
                          '$UNIT_TEST_ROOT/${CONFIG}_${TARGET_PLATFORM}/${PART_NAME}_${PART_VERSION}/$UNIT_TEST_TARGET/',
                          'Full directory used for a given unit test run'
                          )
api.register.add_list_variable('UTEST_CMDARGS', [], '')
api.register.add_variable('UNIT_TEST_ENV',
                          {'UNIT_TEST_DIR': '${ABSPATH("$UNIT_TEST_DIR")}'},
                          'Default values add to default environment when running unit tests')
api.register.add_variable('UNIT_TEST_TARGET_NAME',
                          '${PART_NAME}-${UNIT_TEST_TARGET}_${PART_VERSION}',
                          'Default value of a given unit test executable')
api.register.add_variable('UNIT_TEST_SCRIPT_NAME',
                          '${UNIT_TEST_TARGET}',
                          'Default value of a given unit test executable')
api.register.add_variable(
    'UNIT_TEST_RUN_SCRIPT_COMMAND',
    'cd ${NORMPATH("$UNIT_TEST_DIR")} && ${RELPATH("INSTALL_BIN", "UNIT_TEST_DIR")}${UNIT_TEST_TARGET_NAME} ${UTEST_CMDARGS}',
    'Command action used to run a unit test script in SCons run_utest::')
api.register.add_variable('UNIT_TEST_RUN_COMMAND',
                          '${RELPATH("INSTALL_BIN","UNIT_TEST_DIR")}${UNIT_TEST_TARGET_NAME} ${UTEST_CMDARGS}',
                          'Command action used to run a unit test in the script')
api.register.add_variable('RUN_UTEST_EXIT_FUNCTION',
                          run_utest_return_default,
                          'Function that will do custom mapping of return code')
