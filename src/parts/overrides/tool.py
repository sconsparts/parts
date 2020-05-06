# this override fixes some issue with tools being reloaded
# and imporve report handling when a tools fails


import imp
import sys
import traceback
from collections import defaultdict

import parts.api as api
import SCons.Tool
from SCons.Debug import logInstanceCreation


class Parts_Tool(object):
    _cache = defaultdict(dict)

    def __init__(self, name, toolpath=[], **kw):
        if __debug__:
            logInstanceCreation(self)
        self.name = name
        self.toolpath = toolpath + SCons.Tool.DefaultToolpath
        # remember these so we can merge them into the call
        self.init_kw = kw

        module = self._tool_module()
        self.generate = module.generate
        self.exists = module.exists
        if hasattr(module, 'options'):
            self.options = module.options

    def _tool_module(self):
        # TODO: Interchange zipimport with normal initilization for better error reporting

        new_sys_path = sys.path + self.toolpath
        path_key = ''.join(new_sys_path)
        try:
            return Parts_Tool._cache[path_key][self.name]
        except KeyError:
            oldpythonpath = sys.path
            sys.path = list(self.toolpath) + sys.path

            try:
                try:
                    file, path, desc = imp.find_module(self.name, self.toolpath)
                    full_name = "{0}<{1}>".format(self.name, str(path.__hash__()))
                    try:
                        Parts_Tool._cache[path_key][self.name] = result = sys.modules[full_name]
                    except KeyError:
                        pass
                    else:
                        if file:
                            file.close()
                        return result
                    try:
                        Parts_Tool._cache[path_key][self.name] = result = imp.load_module(full_name, file, path, desc)
                    finally:
                        if file:
                            file.close()
                    return result
                except ImportError as e:
                    api.output.verbose_msg("tools", "Failed to load module!")
                    api.output.verbose_msg(["tools_failure", "load_module"], "Stack:\n{0}".format(traceback.format_exc()))

                    if str(e) != "No module named {0}".format(self.name) and str(e) != "No module named '{0}'".format(self.name):
                        raise SCons.Errors.EnvironmentError(e)
                    try:
                        import zipimport
                    except ImportError:
                        pass
                    else:
                        for aPath in self.toolpath:
                            try:
                                importer = zipimport.zipimporter(aPath)
                                Parts_Tool._cache[path_key][self.name] = result = importer.load_module(self.name)
                            except ImportError as e:
                                pass
                            else:
                                return result
            finally:
                sys.path = oldpythonpath

            full_name = 'SCons.Tool.' + self.name
            try:
                Parts_Tool._cache[path_key][self.name] = result = sys.modules[full_name]
            except KeyError:
                try:
                    smpath = sys.modules['SCons.Tool'].__path__
                    try:
                        file, path, desc = imp.find_module(self.name, smpath)
                        Parts_Tool._cache[path_key][self.name] = module = imp.load_module(full_name, file, path, desc)
                        setattr(SCons.Tool, self.name, module)
                        if file:
                            file.close()
                        return module
                    except ImportError as e:
                        if str(e) != "No module named %s" % self.name:
                            api.output.verbose_msg("tools", "Failed to load module!")
                            api.output.verbose_msg(["tools_failure", "load_module"], "Stack:\n%s" % (traceback.format_exc()))
                            raise SCons.Errors.EnvironmentError(e)
                        try:
                            import zipimport
                            importer = zipimport.zipimporter(sys.modules['SCons.Tool'].__path__[0])
                            Parts_Tool._cache[path_key][self.name] = module = importer.load_module(full_name)
                            setattr(SCons.Tool, self.name, module)
                            return module
                        except ImportError as e:
                            m = "No tool named '%s': %s" % (self.name, e)
                            api.output.verbose_msg("tools", "Failed to load module!")
                            api.output.verbose_msg(["tools_failure", "load_module"], "Stack:\n%s" % (traceback.format_exc()))
                            raise SCons.Errors.EnvironmentError(m)
                except ImportError as e:
                    m = "No tool named '%s': %s" % (self.name, e)
                    api.output.verbose_msg("tools", "Failed to load module!")
                    api.output.verbose_msg(["tools_failure", "load_module"], "Stack:\n%s" % (traceback.format_exc()))
                    raise SCons.Errors.EnvironmentError(m)
            else:
                return result

    def __call__(self, env, *args, **kw):
        if self.init_kw is not None:
            # Merge call kws into init kws;
            # but don't bash self.init_kw.
            if kw is not None:
                call_kw = kw
                kw = self.init_kw.copy()
                kw.update(call_kw)
            else:
                kw = self.init_kw
        env.Append(TOOLS=[self.name])
        if hasattr(self, 'options'):
            import SCons.Variables
            if 'options' not in env:
                from SCons.Script import ARGUMENTS
                env['options'] = SCons.Variables.Variables(args=ARGUMENTS)
            opts = env['options']

            self.options(opts)
            opts.Update(env)

        self.generate(env, *args, **kw)

    def __str__(self):
        return self.name

    def Exists(self, env, *args, **kw):
        return self.exists(env, *args, **kw)


SCons.Tool.Tool = Parts_Tool
