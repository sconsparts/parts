import SCons.Script
import parts.api as api

# TODO need to add package group to scan directory
heat_action = SCons.Action.Action("heat.exe dir ${SOURCE} -o ${TARGET}"
                                 " -sw5150 -gg -cg ${TARGET.filebase}Group -srd -sfrag -dr INSTALLFOLDER"# -var var.PartsBuildDir"                                 
                                 )

# internal wix package builder...
api.register.add_builder('_heat',SCons.Builder.Builder(
                    action = heat_action,
                    source_factory = SCons.Node.FS.Dir,
                    source_scanner = SCons.Defaults.DirScanner,
                    suffix = '.wxs',
				    ))


