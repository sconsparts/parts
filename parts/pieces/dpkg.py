
import SCons.Script
import parts.api as api

#-us -uc -b creates binary package without signing the .changes file,
#-d is to avoid running dpkg-checkbuilddeps to check build dependencies
#helpful to run on fedora systems.
dpkg_action = SCons.Action.Action(["cd ${SOURCE} && debuild -us -uc -d -b"])

# internal debian package builder... meant to be called by DPKGPackage function internally
api.register.add_builder('_dpkg',SCons.Builder.Builder(
                    action = dpkg_action,
                    source_factory = SCons.Node.FS.Dir,
                    source_scanner = SCons.Defaults.DirScanner,
                    suffix = '.deb',
				    single_source=True))
