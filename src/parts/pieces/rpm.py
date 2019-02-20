import parts.api as api
import SCons.Script

rpm_action = SCons.Action.Action([
    'mkdir -p ${TARGET.dir}/BUILD',
    ('rpmbuild  --define "_topdir ${TARGET.Dir(\".\").abspath}" '
     '--define "_rpmdir ${TARGET.Dir(\".\").abspath}" '
     '--define "_build_name_fmt %%{Name}-%%{Version}-%%{Release}.%%{Arch}.rpm" -bb '
     '--target=${TARGET_ARCH} ${TARGET.dir}/SPECS/*')])

# internal rpm package builder... meant to be called by RPMPackage function internally
api.register.add_builder('_rpm', SCons.Builder.Builder(
    action=rpm_action,
    source_factory=SCons.Node.FS.Entry,
    target_factory=SCons.Node.FS.File,
    suffix='.rpm')
)
