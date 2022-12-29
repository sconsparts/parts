# stage - prototype
import os
import sys

import parts.api as api
import parts.common as common
import parts.core.util as util
import parts.errors as errors
import parts.pattern as pattern
import SCons.Node

from .context import Context
from .metasection import MetaSection
from .phaseinfo import PhaseInfo


class TestCtx(Context):
    def __init__(self):
        self.Command = None
        self.CommandArgs = None
        self.Target = None
        self.Sources = []
        self.TimeOut = None
        self.DataFiles = []
        self.Env = {}

        super().__init__()


class UnitTest(MetaSection):
    name = "unit_test"
    concepts = ("utest", "run_utest")

    def __init__(self):
        super().__init__()
        self._run_context: Dict[str, TestCtx] = {}

    def PreEnvSetup(self):
        self.Env['BUILD_DIR'] = f"{self.Env['BUILD_DIR']}/${{PHASE_GROUP}}"

    def ProcessSection(self, level):
        '''
        This function must be define to process and load the section logic correctly
        '''
        # we need to see what groups we have as we want to process the groups with different environments
        # to allow each test if it needs to, to add values to allow each test works with little effort from user

        # Get all the groups defined
        groups = self.PhaseGroups()

        for group in groups:           

            # for each group we want a unique environment and test context
            if group not in self._run_context:
                self._run_context[group] = (self.Env.Clone(), TestCtx())

            env, context = self._run_context[group]
            srcDir = env.AbsDir('.')
            build_dir_leaf = group
            build_dir = env.Dir(f"${{BUILD_DIR}}/{build_dir_leaf}")
            env.fs.VariantDir(build_dir, env.Dir(srcDir), env['duplicate_build'])

            # this is the items outside the src_dir area
            oot_build_dir = env.Dir(f"${{BUILD_DIR}}/{build_dir_leaf}/oot")
            env['OUTOFTREE_BUILD_DIR'] = f"${{BUILD_DIR}}/{build_dir_leaf}/oot"

            env.VariantDir(variant_dir=oot_build_dir, src_dir="#", duplicate=env['duplicate_build'])

            build_dir._create()
            try:
                env.fs.chdir(build_dir, change_os_dir=True)
            except:
                env.fs.chdir(build_dir, change_os_dir=False)
            context._lock()

            ##############################################
            # process build phase
            if self.isPhasedGroupDefined("build", group):
                self.ProcessPhase("build", group)
            
            #####################################
            # process run phase
            self.ProcessPhase("run", group)
            # validate the context for the group
            context._unlock()

            self._section.DefiningPhase = ("_post", group)

            # process the extra stuff

            # tweak Environment
            env['UNIT_TEST_TARGET'] = group

            # make a batch_key for the CCopy() call to help with overall speed
            batch_key_base = hash(self.name), hash(self.Part.Alias), hash(group)
            
            # if not context.Command:
            # need to get a stack to point to the parts file for this....
            #api.output.error_msg("test.Command was not defined for the run phase. Don't know what to run for the test!")

            if not context.Target and not context.Sources:
                api.output.error_msg("A test must define a target node or set of sources to build for the test\n "
                                     "Please define test.Target or test.Sources")
            elif context.Target and context.Sources:
                api.output.error_msg("A test cannot define both test.Target and test.Sources\n Please choose one.")
            # elif util.isList(context.Target) and len(context.Target) > 1:
            #    api.output.error_msg("test.Target must be a single node")
            elif context.Target:
                if util.isDir(context.Target) or util.isDir(context.Target[0]):
                    api.output.error_msg("test.Target must be a file base node, not a directory node")
                elif util.isAlias(context.Target) or util.isAlias(context.Target[0]):
                    api.output.error_msg("test.Target must be a file base node, not a alias node")
                elif util.isValue(context.Target) or util.isValue(context.Target[0]):
                    api.output.error_msg("test.Target must be a file base node, not a value node")
                elif util.isList(context.Target):
                    target = env.CCopyAs(f"_target_rename_/${{UNIT_TEST_TARGET_NAME}}{context.Target[0].suffix}", context.Target[0], CCOPY_BATCH_KEY=batch_key_base)
                    target += target[1:]
                elif util.isEntry(context.Target):
                    target = context.Target
                    target = env.CCopyAs("_target_rename_/$UNIT_TEST_TARGET_NAME", target, CCOPY_BATCH_KEY=batch_key_base)
            elif context.Sources:
                context.Sources = common.make_list(context.Sources)
                context.Sources = [src if not isinstance(src, pattern.Pattern) else src.files() for src in context.Sources]

                target = env.Program(f"{env['UNIT_TEST_TARGET_NAME']}", context.Sources)

            # copy the target

            ret = []
            for i in target:
                # if util.isFile(i) or isNode(i) or util.isString(i):
                if common.is_category_file(env, 'INSTALL_LIB_PATTERN', i):
                    ret += env.CCopy(target='$INSTALL_LIB', source=i, CCOPY_BATCH_KEY=(*batch_key_base, hash("install")))
                else:
                    ret += env.CCopy(target='$INSTALL_BIN', source=i, CCOPY_BATCH_KEY=(*batch_key_base, hash("install")))

            #####################################################
            # copy any datafile to the testing sandbox
            # should clean up this look as it a common C&P we have
            # flatten the sources
            data_src = env.Flatten(context.DataFiles or [])
            out = []
            dest_dir = env.Dir("$UNIT_TEST_DIR")
            for s in data_src:
                if isinstance(s, pattern.Pattern):
                    t, sr = s.target_source(dest_dir)
                    out += env.CCopyAs(target=t, source=sr, CCOPY_BATCH_KEY=(*batch_key_base, hash("data")))
                    # print "Pattern type"
                elif isinstance(s, SCons.Node.FS.Dir):
                    # get all file in the directory
                    # ... add code...
                    out += env.CCopy(target=dest_dir, source=s, CCOPY_BATCH_KEY=(*batch_key_base, hash("data")))
                elif isinstance(s, SCons.Node.FS.File) or isinstance(s, SCons.Node.Node):
                    if s.srcnode().has_builder:
                        # this node is built.. use the srcnode to deal with out
                        # node that are from a different section
                        out += env.CCopy(target=dest_dir, source=s.srcnode(), CCOPY_BATCH_KEY=(*batch_key_base, hash("data")))
                    else:
                        out += env.CCopy(target=dest_dir, source=s, CCOPY_BATCH_KEY=(*batch_key_base, hash("data")))
                elif util.isString(s):
                    f = env.subst(s)
                    if f.startswith(("../")):
                        f = env.AbsFileNode(f)
                    out += env.CCopy(target=dest_dir, source=f, CCOPY_BATCH_KEY=(*batch_key_base, hash("data")))
                else:
                    api.output.warning_msg("Unknown type in unit_test section in Part", env.subst('$PART_NAME'))

            ###############################################################
            # call the script generator to define the wrapper scripts to
            # build for this making testing more automatable.

            # in case a python script is being called.. it is the same version of python as we are using
            env.PrependENVPath('PATH', os.path.split(sys.executable)[0], delete_existing=True)

            # this builder makes the scripts to run the test on
            # the command line with ease
            for k, v in env.get('UNIT_TEST_ENV', {}).items():  # DOUBLE CHECK THIS LOGIC
                env['ENV'][k] = env.subst(v)

            # make command args string
            if context.CommandArgs:
                env['UTEST_CMDARGS'] = context.CommandArgs

            scripts_out = env.__UTEST__(
                f"_scripts_/{env['UNIT_TEST_SCRIPT_NAME']}",
                [],  # no sources minus the "actions sig"
                # Need to convert UNIT_TEST_ENV dictionary into a list
                # of (key, value) pairs to make SCons correctly track changes
                # in its contents.
                UNIT_TEST_ENV=list(env.get('UNIT_TEST_ENV', {}).items())

            )
            # copy the script to the testing area to run later
            # group this with the data files.. should be safe
            scripts_out = env.CCopy("$UNIT_TEST_DIR", scripts_out, CCOPY_BATCH_KEY=(*batch_key_base, hash("data")))

            ##########################################
            # run command
            core_alias = env.Alias('${BUILD_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::${UNIT_TEST_TARGET}')
            core_run_alias_env = env.Override(
                dict(
                    TIME_OUT=env.get("RUN_UTEST_TIME_OUT", env.get('TIME_OUT')),
                    LOG_PART_FILE_NAME=f'run_utest.{ret[0].name}.log'
                )
            )

            def wrap_exit_code_function(function, env, stackframe):
                '''
                SCons.Action object accepts exitstatfunc argument to be a callable
                with returncode as its only parameter. We want to pass some more arguments
                to our function.
                '''
                return lambda rcode: function(rcode, env=env, stackframe=stackframe)

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
            env.AlwaysBuild(core_run_alias)

            # map out various "extra" Aliases

            base_run_alias = env.Alias('${RUN_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}', core_run_alias)
            env.AlwaysBuild(base_run_alias)

            recurse_run_alias = env.Alias('${RUN_UTEST_CONCEPT}${PART_ALIAS_CONCEPT}${PART_ALIAS}::', base_run_alias)
            env.AlwaysBuild(recurse_run_alias)

            # map the recursive up the chain of parents if any
            talias_run = common.map_alias_to_root(self.Part, 'run_utest', '{0}::${{PART_ALIAS_CONCEPT}}{1}::')
            env.AlwaysBuild(talias_run)

            r = env.Alias('${RUN_UTEST_CONCEPT}', talias_run)
            env.AlwaysBuild(r)

            self._section.DefiningPhase = None

    def BuildSetup(self, callback, group):
        '''
        need custom setup for configure phases
        '''
        env = self._run_context[group][0]
        callback(env)

    def RunSetup(self, callback, group):
        '''
        need custom setup for configure phases
        '''
        env, test = self._run_context[group]
        callback(env, test)


api.register.add_section(
    metasection=UnitTest,
    target_mapping_logic=api.register.GroupLogic.GROUPED,
    phases=[
        PhaseInfo(
            name="build",
            optional=False,
            setup_func=UnitTest.BuildSetup,
        ),
        PhaseInfo(
            name="run",
            optional=False,
            requires_group=True,
            setup_func=UnitTest.RunSetup,
            dependson_phases=['setup', 'build'],
        ),
    ]
)
