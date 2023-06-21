# this is a set of scanner that are generally useful
import json

import parts.api as api
import parts.common as common
import parts.glb as glb
import parts.node_helpers as node_helpers
import SCons.Script
from parts.core.states import ChangeCheck

# this is a general scanner for files on disk.
# useful for dealing with Commands that might or might not trigger
# when certain sources changed. This allows a command or build to trigger
# based on a known set.


def SourceScanner(patterns):
    patterns = common.make_list(patterns)

    def scanner_func(node, env, path):
        ret = []
        for pattern in patterns:
            ret += pattern.files()
        return ret

    return SCons.Script.Scanner(scanner_func)


NullScanner = SCons.Script.Scanner(function=lambda *lst, **kw: [], name="NullScanner", scan_check=lambda *lst, **kw: False)

#####

# go over the depends


def depends_sdkfiles_scanner(node, env, path):
    # The generation of the makefile depends on any dependent components being built enough for any configure logic to work
    # The easiest way to deal with this is to depend on the files SDK that would exists as part of the SDK being build. In
    # the case of raw make files with no configure logic it will assume the dependants exists. This mean we have to force
    # a depends to have that components fully built as we cannot depend scanners to get everything that is needed.
    # (ie writing a Makefile/cmake or autoconf scanner could fix this, but is a very difficult it not near impossible task).
    # Making this less fine grain depends corrects the problem has should have minimal impact on SCons being able to build
    # quickly with -j
    import parts.core.builders as builders  # needed here because python3.6 has a loading issue
    api.output.verbose_msgf(["scanner.sdk", "scanner", "scanner.called"], "Scanning node {0}", node.ID)
    # get the section
    sec = glb.engine._part_manager._from_env(env).Section(env["PART_SECTION"])
    ret = []
    file_list = []
    # for each component 
    for comp in sec.Depends:
        # do we have a match? Might be optional so we don't care
        if not comp.hasUniqueMatch and comp.isOptional:
            continue
        # get the export.jsn finle
        lenv = comp.Section.Env
        export_file = lenv.File(builders.exports.file_name)

        if hasattr(export_file.attributes,"_is_dyn_generated"):
            api.output.verbose_msgf(["scanner.sdk", "scanner",], f"{node.ID} needs to be dynamically scanned")
            node.scan()

        # is the export file up-to-date?
        # if node_helpers.has_changed(export_file, skip_implicit=False) & ChangeCheck.SAME:
        #     # Then load jsn file and parse out the SDK items (This should be faster than trying to do a "glob/Pattern" of the files in the directories")
        #     api.output.verbose_msgf(["scanner.sdk", "scanner"], "Loading {}", export_file)
        #     with open(export_file.ID) as infile:
        #         data = json.load(infile)

        #     for k, files in data.items():
        #         if k.startswith("SDK") and k != "SDK":
        #             for f in files:
        #                 ret.append(lenv.File(f))
        # else:
        #     api.output.verbose_msgf(["scanner.sdk", "scanner"], "Skipping {} because it is out of date", comp.Section.ID)

        file_list.append(export_file)
    finial_ret = file_list#+ret
    api.output.verbose_msgf(["scanner.sdk", "scanner"], "returning {}", common.DelayVariable(lambda: [e.ID for e in finial_ret]))
    return finial_ret


DependsSdkScanner = SCons.Script.Scanner(depends_sdkfiles_scanner, name="DependsSdkScanner")


api.register.add_global_parts_object("NoneScanner", NullScanner)
api.register.add_global_object("NoneScanner", NullScanner)
api.register.add_global_parts_object("NullScanner", NullScanner)
api.register.add_global_object("NullScanner", NullScanner)

api.register.add_global_parts_object("DependsSdkScanner", DependsSdkScanner)
api.register.add_global_object("DependsSdkScanner", DependsSdkScanner)

api.register.add_global_parts_object("SourceScanner", SourceScanner)
api.register.add_global_object("SourceScanner", SourceScanner)
