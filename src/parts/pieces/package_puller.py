import os
import subprocess
import sys

import parts.api as api
import parts.common as common

#yum -y install --downloadonly --downloaddir=<dir> <packagename>
# dnf download <packagename> 
# add --resolve for dependancies of dnf package


class import_rpm_files:
    def __init__(self, env):
        self.env = env

    def __call__(self, rpms = [], includes = [], excludes = []):

        errors = []
        files = []

        if len(rpms) == 0:
            rpms = [self.env.subst("${STACK_NAMESPACE}${STACK_VESION}-$PART_NAME-$PART_VERSION").replace("_", "-"),
                    self.env.subst("${STACK_NAMESPACE}${STACK_VESION}-$PART_NAME$RPM_DEVEL_EXT-$PART_VERSION").replace("_", "-")]

        for rpm in rpms:
            api.output.verbose_msg(["import_rpm_files"], "[{}] rpm -ql {}".format('CMD', rpm))
            result = subprocess.run(['rpm', '-ql', rpm], stdout=subprocess.PIPE)
            str = result.stdout.decode('utf-8')

            api.output.verbose_msg(["import_rpm_files"], "[{}]\n----\n{}----".format('OUTPUT', str))

            if str.find("package {} is not installed".format(rpm)) == 0:
                api.output.verbose_msg(["import_rpm_files"], "[{}] Not installed: {}".format('MISSING', rpm))
                errors.append(f"Please install {rpm}\n Run: sudo yum install {rpm}")
                failed = True
            else:
                for file in str.splitlines():
                    if os.path.isfile(file):
                        api.output.verbose_msg(["import_rpm_files"], "[{}] {}".format('CHECKING', file))
                        excluded = False
                        for exclude in excludes:
                            if file.startswith(exclude):
                                excluded = exclude
                        if excluded != False:
                            api.output.verbose_msg(["import_rpm_files"], "[{}] {} [{}]".format('EXCLUDED', file, excluded))
                        elif file.startswith(self.env.subst("${PACKAGE_SOURCE}")):
                            inc = file.find('/src/')
                            if inc:
                                offset = ((len(file) - (inc + len('/src/'))) * -1)
                                sub_dir = os.path.dirname(file[offset:])
                                api.output.verbose_msg(["import_rpm_files"], "[{}] {}, subdir={}".format('SRC', file, sub_dir))
                                self.env.SdkSource(file, sub_dir=sub_dir)
                            else:
                                api.output.verbose_msg(["import_rpm_files"], "[{}] {}, subdir={}".format('SRC', file, sub_dir))
                                self.env.SdkSource(file)
                        elif common.is_category_file(self.env, 'SDK_LIB_PATTERN', file):
                            basename = os.path.basename(file)
                            if basename.startswith("lib"):
                                dirname = os.path.dirname(file)
                                libdir = "{}/{}".format(self.env.subst("${PACKAGE_ROOT}"), self.env.subst("${INSTALL_LIB_SUBDIR}"))

                                if dirname == libdir:
                                    api.output.verbose_msg(["import_rpm_files"], "[{}] {}".format('LIB', file))
                                    self.env.SdkLib(file)
                                else:
                                    api.output.verbose_msg(["import_rpm_files"], "[{}] dirname: {}, libdir: {}".format('LIB', dirname, libdir))
                                    sub_dir = dirname[len(libdir) + 1:]
                                    api.output.verbose_msg(["import_rpm_files"], "[{}] {}, sub_dir: {}".format('LIB', file, sub_dir))
                                    self.env.SdkLib(source=file, sub_dir=sub_dir)
                                    if os.path.islink(file):
                                        target = os.readlink(file)
                                        if target.startswith("lib") == False:
                                            link = "{}/{}".format(dirname, os.readlink(file))
                                            #link = os.readlink(file)
                                            api.output.verbose_msg(["import_rpm_files"], "[{} : SYMLINK] {} => {}".format('LIB', file, link))
                                            self.env.SdkLib(link, sub_dir=sub_dir)


#                            if basename.startswith("lib") or basename.endswith(".so"):
#                                libdir = "{}/{}".format(self.env.subst("${PACKAGE_ROOT}"), self.env.subst("${INSTALL_LIB_SUBDIR}"))
#                                if dirname == libdir:
#                                    api.output.verbose_msg(["import_rpm_files"], "[{}] {}".format('LIB', file))
#                                    self.env.SdkLib(file)
#                                else:
#                                    api.output.verbose_msg(["import_rpm_files"], "[{}] dirname: {}, libdir: {}".format('LIB', dirname, libdir))
#                                    sub_dir = dirname[len(libdir) + 1:]
#                                    api.output.verbose_msg(["import_rpm_files"], "[{}] {}, sub_dir: {}".format('LIB', file, sub_dir))
#                                    self.env.SdkLib(source=file, sub_dir=sub_dir)
#
                                #if os.path.islink(file):
                                #    link = "{}/{}".format(os.path.dirname(file), os.readlink(file))
                                #    api.output.verbose_msg(["import_rpm_files"], "[{} : SYMLINK] {} => {}".format('LIB', file, link))
                                #    self.env.SdkLib(link)
                        elif common.is_category_file(self.env, 'SDK_INCLUDE_PATTERN', file):
                            inc = file.find('/include/')
                            if inc:
                                offset = ((len(file) - (inc + len('/include/'))) * -1)
                                sub_dir = os.path.dirname(file[offset:])
                                api.output.verbose_msg(["import_rpm_files"], "[{}] {}, subdir={}".format('HEADER', file, sub_dir))
                                #sys.exit(255)
                                self.env.SdkInclude(file, sub_dir=sub_dir, add_to_path=False)
                            else:
                                api.output.verbose_msg(["import_rpm_files"], "[{}] {}, subdir={}".format('LIB', file, sub_dir))
                                self.env.SdkLib(file, add_to_path=False)

        for file in includes:
            inc = file.find('/include/')
            if inc:
                offset = ((len(file) - (inc + len('/include/'))) * -1)
                sub_dir = os.path.dirname(file[offset:])
                api.output.verbose_msg(["import_rpm_files"], "[{}] {}, subdir={}".format('HEADER', file, sub_dir))
                self.env.SdkInclude(file, sub_dir=sub_dir, add_to_path=False)
            else:
                api.output.verbose_msg(["import_rpm_files"], "[{}] {}, subdir={}".format('HEADER', file, ''))
                self.env.SdkInclude(file, sub_dir='', add_to_path=False)

        if len(errors):
            for error in errors:
                api.output.error_msg(error, show_stack=False)
                sys.exit(255)

api.register.add_global_parts_object("ImportRPM", import_rpm_files, True)