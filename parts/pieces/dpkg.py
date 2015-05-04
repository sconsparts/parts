
import SCons.Script
import parts.api as api


dpkg_action = SCons.Action.Action(["cd ${SOURCE} && debuild -us -uc -b"])

# internal debian package builder... meant to be called by DPKGPackage function internally
api.register.add_builder('_dpkg',SCons.Builder.Builder(
                    action = dpkg_action,
                    source_factory = SCons.Node.FS.Dir,
                    source_scanner = SCons.Defaults.DirScanner,
                    suffix = '.deb',
				    single_source=True))
