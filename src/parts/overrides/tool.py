# this override fixes some issue with tools being reloaded
# and imporve report handling when a tools fails

import importlib.machinery
import importlib.util

import sys
import os
# import traceback


import parts.api as api
import SCons.Tool
import SCons.Errors


class Parts_Tool:
    def __init__(self, name, toolpath=None, **kwargs) -> None:
        if toolpath is None:
            toolpath = []

        # Rename if there's a TOOL_ALIAS for this tool
        self.name = SCons.Tool.TOOL_ALIASES.get(name, name)
        self.toolpath = toolpath + SCons.Tool.DefaultToolpath
        # remember these so we can merge them into the call
        self.init_kw = kwargs

        module = self._tool_module()
        self.generate = module.generate
        self.exists = module.exists
        if hasattr(module, 'options'):
            self.options = module.options

    def _tool_module(self):
        """Try to load a tool module.

        This will hunt in the toolpath for both a Python file (toolname.py)
        and a Python module (toolname directory), then try the regular
        import machinery, then fallback to try a zipfile.
        """
        oldpythonpath = sys.path
        sys.path = self.toolpath + sys.path
        # These could be enabled under "if debug:"
        # sys.stderr.write(f"Tool: {self.name}\n")
        # sys.stderr.write(f"PATH: {sys.path}\n")
        # sys.stderr.write(f"toolpath: {self.toolpath}\n")
        # sys.stderr.write(f"SCONS.TOOL path: {sys.modules['SCons.Tool'].__path__}\n")
        debug = False
        spec = None
        found_name = self.name
        add_to_scons_tools_namespace = False

        # Search for the tool module, but don't import it, yet.
        #
        # First look in the toolpath: these take priority.
        # TODO: any reason to not just use find_spec here?
        for path in self.toolpath:
            sepname = self.name.replace('.', os.path.sep)
            file_path = os.path.join(path, sepname + ".py")
            file_package = os.path.join(path, sepname)

            if debug: sys.stderr.write(f"Trying: {file_path} {file_package}\n")

            if os.path.isfile(file_path):
                spec = importlib.util.spec_from_file_location(self.name, file_path)
                if debug: sys.stderr.write(f"file_Path: {file_path} FOUND\n")
                break
            elif os.path.isdir(file_package):
                file_package = os.path.join(file_package, '__init__.py')
                spec = importlib.util.spec_from_file_location(self.name, file_package)
                if debug: sys.stderr.write(f"PACKAGE: {file_package} Found\n")
                break
            else:
                continue

        # Now look in the builtin tools (SCons.Tool package)
        if spec is None:
            if debug: sys.stderr.write(f"NO SPEC: {self.name}\n")
            spec = importlib.util.find_spec("." + self.name, package='SCons.Tool')
            if spec:
                found_name = 'SCons.Tool.' + self.name
                add_to_scons_tools_namespace = True
            if debug: sys.stderr.write(f"Spec Found? .{self.name}: {spec}\n")

        if spec is None:
            # we are going to bail out here, format up stuff for the msg
            sconstools = os.path.normpath(sys.modules['SCons.Tool'].__path__[0])
            if self.toolpath:
                sconstools = ", ".join(self.toolpath) + ", " + sconstools
            msg = f"No tool module '{self.name}' found in {sconstools}"
            raise SCons.Errors.UserError(msg)

        # We have a module spec, so we're good to go.
        module = importlib.util.module_from_spec(spec)
        if module is None:
            if debug: sys.stderr.write(f"MODULE IS NONE: {self.name}\n")
            msg = f"Tool module '{self.name}' failed import"
            raise SCons.Errors.SConsEnvironmentError(msg)

        # Don't reload a tool we already loaded.
        sys_modules_value = sys.modules.get(found_name, False)

        found_module = None
        if sys_modules_value and sys_modules_value.__file__ == spec.origin:
            found_module = sys.modules[found_name]
        else:
            # Not sure what to do in the case that there already
            # exists sys.modules[self.name] but the source file is
            # different.. ?
            sys.modules[found_name] = module
            spec.loader.exec_module(module)
            if add_to_scons_tools_namespace:
                # If we found it in SCons.Tool, add it to the module
                setattr(SCons.Tool, self.name, module)
            found_module = module

        if found_module is not None:
            sys.path = oldpythonpath
            return found_module

        sys.path = oldpythonpath

        # We try some other things here, but this is essentially dead code,
        # because we bailed out above if we didn't find a module spec.
        full_name = 'SCons.Tool.' + self.name
        try:
            return sys.modules[full_name]
        except KeyError:
            try:
                # This support was added to enable running inside
                # a py2exe bundle a long time ago - unclear if it's
                # still needed. It is *not* intended to load individual
                # tool modules stored in a zipfile.
                import zipimport

                tooldir = sys.modules['SCons.Tool'].__path__[0]
                importer = zipimport.zipimporter(tooldir)
                if not hasattr(importer, 'find_spec'):
                    # zipimport only added find_spec, exec_module in 3.10,
                    # unlike importlib, where they've been around since 3.4.
                    # If we don't have 'em, use the old way.
                    module = importer.load_module(full_name)
                else:
                    spec = importer.find_spec(full_name)
                    module = importlib.util.module_from_spec(spec)
                    importer.exec_module(module)
                sys.modules[full_name] = module
                setattr(SCons.Tool, self.name, module)
                return module
            except zipimport.ZipImportError as e:
                msg = "No tool named '{self.name}': {e}"
                raise SCons.Errors.SConsEnvironmentError(msg)

    def __call__(self, env, *args, **kw) -> None:
        if self.init_kw is not None:
            # Merge call kws into init kws;
            # but don't bash self.init_kw.
            if kw is not None:
                call_kw = kw
                kw = self.init_kw.copy()
                kw.update(call_kw)
            else:
                kw = self.init_kw
        env.AppendUnique(TOOLS=[self.name])
        if hasattr(self, 'options'):
            import SCons.Variables
            if 'options' not in env:
                from SCons.Script import ARGUMENTS
                env['options'] = SCons.Variables.Variables(args=ARGUMENTS)
            opts = env['options']

            self.options(opts)
            opts.Update(env)

        self.generate(env, *args, **kw)

    def __str__(self) -> str:
        return self.name
    
    def Exists(self, env, *args, **kw):
        return self.exists(env, *args, **kw)

SCons.Tool.Tool = Parts_Tool
