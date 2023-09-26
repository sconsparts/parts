

import atexit
import copy
import gc
import hashlib
import os
import pprint
import stat
import sys
import time

import parts.api as api
import parts.api.output
import parts.common as common
import parts.core.util as util
import parts.core.builders  # load the core builders
import parts.core.util.getcontent as getcontent
import parts.datacache as datacache
import parts.errors as errors
import parts.events as events
import parts.glb as glb
import parts.load_module as load_module
import parts.logger as logger
import parts.overrides as overrides
import parts.part_manager as part_manager
import parts.pnode as pnode
import parts.poptions as poptions  # want to remove
import parts.target_type as target_type
import parts.Variables as Variables
import parts.version_info as version_info
import SCons.Node.FS
import SCons.Script
from SCons.Debug import logInstanceCreation
from SCons.Script.Main import memory_stats
from SCons.Util import flatten

################################################################################


def get_Sconstruct_files():
    '''
    get the names of all the "top level" SConstruct files being processed
    Need to see if there is a better SCons function for this
    '''
    # Get the name of the SConstruct file... as the user mighthave used -F
    fnames = SCons.Script.GetOption('file')

    if not fnames:
        # check current directory to see if what "default" file exits
        if os.path.exists("SConstruct"):
            fnames = ["SConstruct"]
        elif os.path.exists("Sconstruct"):
            fnames = ["Sconstruct"]
        elif os.path.exists("sconstruct"):
            fnames = ["sconstruct"]

    return fnames


def is_Sconstruct_up_to_date():
    '''
    This functions will tell us if the Sconstruct file looks as if it has changed
    by checking the MD5
    '''

    fnames = get_Sconstruct_files()
    data = datacache.GetCache("global_data")
    ret = True
    if data is None:
        api.output.verbose_msg("update_check", 'No datacache For SConstruct file found')
        return False
    for i in fnames:
        try:
            tmp = data['sconstruct_files'][i]
        except KeyError:
            # should not happen... but the file have been updated during development
            return False
        # see if the part file is different
        if os.path.isfile(i):
            # it should exist
            if os.stat(i)[stat.ST_MTIME] != tmp['timestamp']:
                # time stamp is different .. check csig to be sure
                if glb.engine.def_env.File(i).get_csig() != tmp['csig']:
                    api.output.verbose_msg("update_check", "File: %s has changed" % (i))
                    ret = False
        else:
            api.output.verbose_msg("update_check", 'File: %s does not exist' % (i))
            ret = False

    return ret

# would it be nice if there was a addon base in Scons... hmmmmm


class parts_addon:

    def __init__(self):
        if __debug__:
            logInstanceCreation(self)

        # some known data items
        self.__part_manager:part_manager.part_manager = None
        self.__def_env = None
        self.__post_process_queue = []
        self.__cache_key = None
        self.__build_mode = None
        self.__had_error = None
        self.__is_sconstruct_loaded = False

        self._exit_up_to_date = False
        self._build_files_loaded = False

        # events
        self.CacheDataEvent = events.Event()
        self.CacheDataEvent += self._store_global_data
        self.SConstructLoadedEvent = events.Event()
        self.PostProcessEvent = events.Event()

        # start up the reporter which controls the streams and all output
        use_color = SCons.Script.GetOption('use_color')
        # need to trace this before we set the colors else the tests break
        api.output.trace_msg("use_color_option", "use_color =", use_color)
        redirected = os.isatty(sys.__stdout__.fileno()) == False or os.isatty(sys.__stderr__.fileno()) == False
        if use_color is not None and 'defaults' in use_color and redirected:
            use_color = False

        log_obj = logger.QueueLogger
        log_obj = log_obj('', '')
        try:
            verbose = [i.lower() for i in SCons.Script.GetOption('verbose')]
        except Exception:
            verbose = []
        try:
            trace = [i.lower() for i in SCons.Script.GetOption('trace')]
        except Exception:
            trace = []

        glb.rpter.Setup(
            log_obj,
            silent=SCons.Script.GetOption('silent'),
            verbose=verbose,
            trace=trace,
            use_color=use_color
        )

    def Start(self):
        api.output.verbose_msg("init", "Starting up Parts")
        # set up some globals
        glb.pnodes = pnode.pnode_manager.manager()

        poptions.post_option_setup()
        # setup variable
        self._setup_variables()
        # setup command line arguments
        self._setup_arguments()
        # setup default Environment overides
        api.output.verbose_msg("startup", "Creating default environment")
        SCons.Script.DefaultEnvironment()
        # turn off all default building of any items without a target, or until
        # default is called again to set one. ( ie the default by Scons is '.' which is everything)
        self.def_env.Default('')
        self.def_env.EnsureSConsVersion(4, 4, 0)

        # try to setup all logger
        self._setup_logger()
        # generate help text
        if self.__build_mode == 'help':
            self._setup_help_info()
        # setup the sdk options
        # self._setup_sdk()
        # setup the progress meter
        self._setup_progress_meter()

        # setup managers
        self.__part_manager = part_manager.part_manager()

        api.output.verbose_msg("init", "Registering exit handler")
        atexit.register(self.ShutDown)

        # this is work around to SCons loading the python executable as a node
        # and seeing it as a File Node when in cases it might be a Symbolic link
        # there is this case in which SCons will store this as the incorrect type.
        node = self.def_env.File(sys.executable)
        node.disambiguate()
        

        # this is a hack to get around an issue with stuff like the extract builder that would create
        # a a.sconsign.dblite file in the wrong directory as a side effect of the variant direct change of
        # the CWD bug in SCons
        # self.def_env.File(get_Sconstruct_files()[0]).get_csig()

    def ShutDown(self):

        # if we exit because we are up-to-date... just exit
        if self._exit_up_to_date or self.__build_mode == 'help' or self.__build_mode == 'question':
            return

        # write out data cache files..given nothing went wrong and
        # we had something to build
        # check to see that we even have targets to process, and that there are no error conditions
        if SCons.Script.BUILD_TARGETS:  # and SCons.Script.Main.exit_status == 0 and self.HadError==False and self.__use_cache == True:
            # current changed logic to say the build is good if we loaded all the information we had to load.
            # given this we don't really care if there was a bad "build" as the state we care about should be OK
            # self.store_db_data(self._build_files_loaded,self.__build_mode)
            pass
        # else:
        #    self.store_db_data(False)
        # datacache.SaveCache()
        # get what went wrong if anything
        bf_lst = SCons.Script.GetBuildFailures()

        # report what went wrong if anything
        if bf_lst:
            bf_lst_len = len(bf_lst)
            msg = ''
            for bf in bf_lst:
                if util.isList(bf.command):
                    cmd = ' '.join(bf.command)
                else:
                    cmd = bf.command
                for node in flatten(bf.node):
                    pinfo = self._part_manager._from_env(node.env)
                    if pinfo:
                        msg += ' Part:"{0}"\n Target:"{1}"\n Config:"{2}"\n Node:"{3}"\n'.format(pinfo.Name,
                                                                                                 node.env['TARGET_PLATFORM'],
                                                                                                 node.env['CONFIG'],
                                                                                                 node)
                    else:
                        msg += 'Node: "{0}"\n'.format(bf.node)

            api.output.error_msg("Summary: {0} build failure detected during build\n{1}".format(
                bf_lst_len, msg), show_stack=False, exit=False)

        glb.rpter.ShutDown()

    def UpToDateExit(self):
        # do a exit because everything is up-to-date
        self._exit_up_to_date = True
        # the question is what kind of exit to do.. hard or soft
        # Scons would prefer the soft.. however it looks like
        # state can get messed up here, so the hard case maybe better
        exit(0)  # hard exit
        # self.def_env.Exit(0) # soft exit()

    def Process(self, fs, options, targets, target_top):
        '''
        This does the main processing of the parts before SCons takes over again
        The main goal of this function to do any post Sconstruct reading processing
        that we might want to do, such as processing the part files,
        delayed mapping, etc
        '''
        memory_stats.append('before Parts processed')
        try:
            self.__had_error = False
            # generate the cache key
            self.generate_cache_key()
            # set state sconstruct to loaded
            self.__is_sconstruct_loaded = True
            # call event that we are loaded
            self.SConstructLoadedEvent(self.__build_mode)
            try:
                targets = SCons.Script.BUILD_TARGETS
                # check to see that we even have targets to process
                if targets == []:
                    return

                # set stack info for reporting issues
                # errors.SetPartStackFrameInfo()

                # If the logger is not being used we want to remove the
                # queue logger to save memory
                if glb.rpter.logger is logger.QueueLogger:
                    # this should reset QueueLogger
                    glb.rpter.logger = logger.nil_logger

                # process the Parts if any exist
                self.__part_manager.ProcessParts()

                # process Queue
                self.parts_process_queue()
                self.PostProcessEvent(self.__build_mode)

                # datacache.SaveCache()
                self._build_files_loaded = True

                # clear the datacache for certain cases that we don't need to touch any more
                # to save memory
                datacache.ClearCache(key="scm")

                if sys.platform == 'win32':
                    # Allow us to prevent error dialog boxes.. useful for running programs such as tests
                    import ctypes
                    tmp = ctypes.windll.kernel32.SetErrorMode(0)
                    ctypes.windll.kernel32.SetErrorMode(tmp | 0x0001 | 0x0002 | 0x0008)

                # reset our stack info for error reporting.. (todo. double check this again)
                # errors.ResetPartStackFrameInfo()
            except Exception:
                self.__had_error = True
                raise
        finally:
            memory_stats.append('after Parts processed')
            api.output.console_msg("\r")  # clears the console value for cleaner printing

    def parts_process_queue(self):

        memory_stats.append('Before post logic queue processing')
        try:
            # process any data we have to post process
            if self.__post_process_queue != []:
                api.output.print_msg("Processing post logic queue")
                total = len(self.__post_process_queue) * 1.0
                cnt = 0
                msg = '{0}/{1}'.format(cnt, total)
                api.output.console_msg(" Processing post logic queue %3.2f%% %s \033[K" % ((cnt / total * 100), msg))
                for cnt, i in enumerate(self.__post_process_queue, 1):
                    msg = '{0}/{1} '.format(cnt, total)
                    api.output.verbose_msg(["post_process_queue"],
                                           "Processing post logic queue {0:.2%} {1}".format((cnt / total), msg))
                    api.output.console_msg(" Processing post logic queue {0:.2%} {1} \033[K".format((cnt / total), msg))
                    i()

                msg = '{0}/{1}'.format(cnt, total)
                api.output.console_msg(" Processing post logic queue {0:.2%} {1} \033[K".format((cnt / total), msg))
                self.__post_process_queue = []
                api.output.print_msg("Processing post logic queue finished!")
        finally:
            memory_stats.append('After post logic queue processed')

    def store_db_data(self, goodexit, build_mode):

        # store each part we know about information
        # call Part manager to do this
        api.output.print_msg("Storing Data Cache")
        st = time.time()
        overrides.script_main_debugtime.pre_parts_cache_storing = st
        self.CacheDataEvent(goodexit, build_mode)
        api.output.verbose_msg(['cache_save'], "Fill time=", time.time() - st)
        st = time.time()
        datacache.SaveCache()
        api.output.verbose_msg(['cache_save'], "Save time=", time.time() - st)
        api.output.print_msg("Done -- Storing Data Cache")

    def _store_global_data(self, goodexit, build_mode):
        if build_mode == 'question':
            return
        if goodexit:

            global_data = {}

            # get SConstruct file data ( maybe more than one )
            # we store a dictionary of
            # {<Sconstruct path w/name>:
            #       {
            #           csig:<value>
            #           timestamp:<value>
            #       }
            # }

            # Store ninfo about the SConstruct file
            tmp = {}
            for i in get_Sconstruct_files():
                i = self.def_env.File(i)
                tmp[i.path] = {
                    'csig': i.get_csig(),
                    'timestamp': i.get_timestamp()
                }
            # add to global data
            global_data['sconstruct_files'] = tmp

            # store data in Cache
            datacache.StoreData('global_data', global_data)

    # setup APIs
    def _setup_variables(self):
        '''
        Set all the variable that we have or need globally
        '''

        # set up the build mode
        args = sys.argv[1:]

        api.output.verbose_msg("startup", "Setting building mode")
        if SCons.Script.GetOption('clean'):
            self.__build_mode = 'clean'
        elif SCons.Script.GetOption('help'):
            self.__build_mode = 'help'
        elif SCons.Script.GetOption('question'):
            self.__build_mode = 'question'
        else:
            self.__build_mode = 'build'

        self.__use_cache = SCons.Script.GetOption("parts_cache")

    def _setup_defenv(self):

        pass

    def _setup_logger(self):

        api.output.verbose_msg("startup", "Processing logger options")
        directory = self.def_env.Dir(self.def_env['LOG_ROOT_DIR'])
        log_obj = SCons.Script.GetOption('logger')

        # compatibility check
        if isinstance(glb.rpter.logger, logger.QueueLogger):
            tmp = self.def_env.get('LOGGER', "NIL_LOGGER")
            if tmp != "NIL_LOGGER":
                directory = self.def_env.Dir(self.def_env['LOG_ROOT_DIR'])
                tmp = self.def_env.subst(tmp)
                # remap old TEXT_LOGGER value
                if tmp == 'TEXT_LOGGER':
                    tmp = self.def_env.subst('$' + tmp)

                mod = load_module.load_module(
                    load_module.get_site_directories('loggers'),
                    tmp,
                    'loggers')
                log_obj = mod.__dict__.get(tmp, logger.QueueLogger)
        # just in case of some not running in a normal build run
        if not log_obj:
            log_obj = logger.nil_logger
        # If the first try at this had nothing we have a Queue logger
        # to store everything we have to report so far
        if isinstance(glb.rpter.logger, logger.QueueLogger):
            # Setup new log object and copy over stored messages
            log_obj = log_obj(directory.abspath, self.def_env['LOG_FILE_NAME'])
            glb.rpter.reset_logger(log_obj)

    def _setup_arguments(self):
        '''
        Setup the main option with the varible that can be used to control it
        with SetOptionDefault or the config file
        '''

        for option_name, env_name in (('target_platform', 'TARGET_PLATFORM'),
                                      ('build_config', 'CONFIG'), ('tool_chain', 'toolchain'), ('mode', 'mode'),
                                      ('ccopy_logic', 'CCOPY_LOGIC')):
            value = SCons.Script.GetOption(option_name)
            if value is not None:
                api.output.verbose_msg('startup', 'Setting {0}:'.format(option_name),
                                       value, 'type:', type(value))
                SCons.Script.ARGUMENTS[env_name] = value

        # this is basically just tests code...
        tmp = SCons.Script.GetOption('target_platform')
        api.output.trace_msg("target_platform_option", "target_platform =", tmp)
        if tmp:
            api.output.trace_msg("target_platform_option_arch", "target_arch =", tmp.ARCH)
            api.output.trace_msg("target_platform_option_os", "target_os =", tmp.OS)

        api.output.trace_msg("build_config_option", "build_config =", SCons.Script.GetOption('build_config'))
        api.output.trace_msg("tool_chain_option", "tool_chain =", SCons.Script.GetOption('tool_chain'))
        api.output.trace_msg("mode_option", "mode =", SCons.Script.GetOption('mode'))
        api.output.trace_msg("ccopy_logic_option", "ccopy_logic =", SCons.Script.GetOption('ccopy_logic'))
        api.output.trace_msg("cfg_file_option", "cfg_file =", SCons.Script.GetOption('cfg_file'))
        api.output.trace_msg("logger_option", "logger =", SCons.Script.GetOption('logger'))
        api.output.trace_msg("show_progress_option", "show_progress =", SCons.Script.GetOption('show_progress'))
        api.output.trace_msg("parts_cache_option", "parts_cache =", SCons.Script.GetOption('parts_cache'))
        api.output.trace_msg("scm_jobs_option", "scm_jobs =", SCons.Script.GetOption('scm_jobs'))
        api.output.trace_msg("update_option", "update =", SCons.Script.GetOption('update'))
        api.output.trace_msg("verbose_option", "verbose =", SCons.Script.GetOption('verbose'))

    # def _setup_sdk(self):
        # return

    def _setup_progress_meter(self):
        api.output.verbose_msg("startup", "Setting up show-progress feature")
        if SCons.Script.GetOption('show_progress'):
            class ProgressCounter:
                def __init__(self):
                    self._time = 0
                    self._st = time.time()
                    self.cnt = 0
                    self._node = None

                def __call__(self, node, *args, **kw):
                    if self._time:
                        tt = time.time() - self._time
                        if time.time() - self._time > 10:

                            glb.rpter.stdwrn(" ****** {0} is took {1} sec to process\n".format(self._node.ID, tt))

                    # glb.rpter.console.Trace.write("Processing {0}\r".format(node.ID))
                    self._time = time.time()
                    self._node = node
                    self.cnt += 1
                    print(f"processed: {node.ID}")
                    glb.rpter.stdconsole(
                        f"processed: {self.cnt} Known:{glb.pnodes.TotalNodes} Percent {(self.cnt/glb.pnodes.TotalNodes)*100.0:.2f}% {self.cnt/(self._time - self._st):.2f}            \r")

            # SCons.Script.Progress(ProgressCounter(), 1)
            SCons.Script.Progress(self.def_env['PROGRESS_STR'], 1, file=glb.rpter.console, overwrite=True)

    def add_preprocess_logic_queue(self, funcobj):
        self.__post_process_queue.append(funcobj)

    def _setup_help_info(self):
        return
        api.output.verbose_msg("startup", "In Help mode, setting up Help values")
        starttext = '\n' + version_info.parts_version_text() + '''
Usage 'scons [scons options] [Parts options] [Targets]
Example: scons config=release foo

Use -H or --help-options for a list of scons options
'''
        cfg_files = [SCons.Script.GetOption('cfg_file')]
        vars = Variables.Variables(cfg_files, args=SCons.Script.ARGUMENTS)
        vars.AddVariables(*common.def_vars)
        SCons.Script.Help(starttext + vars.GenerateHelpText(self.def_env, True))

    def record_variant_source_mapping(self, node):
        self.__variant_source_mapping[node.path] = node.srcnode().path

    def get_variant_source_mapping(self, nodestr):
        try:
            return self.__variant_source_mapping[nodestr]
        except KeyError:
            tmp = datacache.GetCache("global_data")
            if tmp:
                tmpval = tmp.get('variant_src_mapping', {})
                tmpval.update(self.__variant_source_mapping)
                self.__variant_source_mapping = tmpval
                if nodestr not in self.__variant_source_mapping:
                    self.__variant_source_mapping[nodestr] = None
        return self.__variant_source_mapping[nodestr]

    def generate_cache_key(self):

        try:
            tmp = self.__cache_key = SCons.Script.ARGUMENTS['USE_CACHE_KEY']
            return tmp
        except KeyError:
            pass

        data = {}
        # get overides Variables
        vars = {}
        # vars=copy.deepcopy(glb.defaultoverides)
        vars.update(SCons.Script.ARGUMENTS)

        # stuff that is getting mapped in more than one way
        # that needs to be white listed from being part of the cache key
        white_list = [
            'LOGGER',
            'PART_LOGGER',
            "LOG_ROOT_DIR",
            'CONFIG',
            'config',
            'TARGET_PLATFORM',
            'toolchain',
            'tools',
            # 'mode',
            'CCOPY_LOGIC',
            'BUILD_BRANCH',
            'USE_CACHE_KEY',
            'SVN_REVISION',
        ]
        data['variables'] = {}
        for k, v in vars.items():
            if k not in white_list:
                tmp = getcontent.asStr(v)
                data['variables'][k] = tmp

        # set of --options
        # list of arguments we want to process as they might effect build state
        # these items we know effect the build ( should change to list of item we know don't effect the system)
        args_to_process = [
            # 'build_config', # get this from the def env
            'cfg_file',
            'file',
            'mode',
            'repository',
            'site_dir',
            'section_suppression',
            # 'tool_chain', # we use the different value to get a better match for this
            # 'target_platform' # we get this from the def_env
        ]
        data['options'] = {}
        for k in args_to_process:
            v = SCons.Script.Main.OptionsParser.defaults[k]
            if v != getattr(SCons.Script.Main.OptionsParser.values, k):
                tmp = getcontent.asStr(v)
                data['options'][k] = tmp

        # this stuff makes up the core key
        data["platform"] = self.def_env.subst("${CONFIG},${HOST_PLATFORM},${TARGET_PLATFORM}")

        # we want to test which builders we are setting by default
        data["configured_tools"] = []

        for i in self.def_env['CONFIGURED_TOOLS']:
            tmp = self.def_env.get(i.upper().replace("+", "X"))
            if tmp:
                data["configured_tools"].append(getcontent.asStr(tmp))
            else:
                data["configured_tools"].append(i)

        # store the ENV value as this has value that can tell us of differences
        # data['ENV']=getcontent.asStr(dict(self.def_env['ENV']))
        # md5.update(getcontent.asStr(dict(self.def_env['ENV'])))
        # Add default environment csig value...

        # we add information about that parts we have defined.
        # a different set gets a different key
        data['parts'] = []
        for pobj in list(self.__part_manager.parts.values()):
            if pobj.isRoot:
                data['parts'].append(pobj.ID)

        md5 = hashlib.md5()
        md5.update(getcontent.asStr(data).encode())
        self.__cache_key = md5.hexdigest()

    @property
    def _cache_key(self):
        if self.__cache_key is None:
            self.generate_cache_key()
        return self.__cache_key

    @_cache_key.setter
    def _cache_key(self, val):
        self.__cache_key = val

    @property
    def _build_mode(self):
        return self.__build_mode

    @property
    def _part_manager(self,) -> part_manager.part_manager:
        return self.__part_manager

    @property
    def HadError(self):
        if self.__had_error is None:
            SCons.Script.Main.exit_status = 2
            return True

        return self.__had_error

    @HadError.setter
    def HadError(self, value):
        self.__had_error = value

    @property
    def isSconstructLoaded(self):
        return self.__is_sconstruct_loaded

    @property
    def BuildFilesLoaded(self):
        return self._build_files_loaded

    @property
    def def_env(self):
        return self.__def_env

    @def_env.setter
    def def_env(self, value):
        cache_path = None
        if self.__def_env:
            cache_path = self.__def_env._CacheDir_path
        self.__def_env = SCons.Defaults._default_env = value
        # do some tweak that we seem to need for default environments
        self.__def_env._CacheDir_path = cache_path
        # This is backward compatibility for Parts
        self.__def_env['PREPROCESS_LOGIC_QUEUE'] = self.__post_process_queue

        # must have Decider set else we have a state issue in the environment
        # self.def_env.Decider('MD5-timestamp')
        self.def_env.Decider('content')


api.register.add_bool_variable(
    'use_env', False, 'Controls if the shell environment will be used instead of values setup by SCons, and Parts')
api.register.add_bool_variable('duplicate_build', False, 'Controls if the src files are copied to the build area for building')
api.register.add_list_variable('mode', [], 'Values used to control different build mode for a given part')

api.register.add_variable('ALIAS_SEPARATOR', '::', 'separator used to separate namespace concepts from general alias value')

api.register.add_variable('PROGRESS_STR', ['scons: Evaluating | \r',
                                           'scons: Evaluating / \r',
                                           'scons: Evaluating - \r',
                                           'scons: Evaluating \\ \r'],
                          'What is used to show progress state')

# vim: set et ts=4 sw=4 ai ft=python :
