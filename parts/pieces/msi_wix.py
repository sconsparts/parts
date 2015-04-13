import SCons.Script
import parts.api as api

#$env:WIX\bin\heat.exe dir .\_build\debug_win32-x86_64_default_wix -o .\test.wxs -sw5150 -gg -cg ProductComponents -srd -sfrag -dr INSTALLFOLDER -var var.PartsBuildDir
#candle  -dPartsBuildDir=C:\Users\psuman\Documents\parts040715\tests\gold_tests\wixsample6\_build\build_debug_win32-x86_64_wix .\test.wxs
#light .\test.wixobj


heat_action = SCons.Action.Action("heat.exe dir .\_build\\build_debug_win32-x86_64_wix -o .\_build\\build_debug_win32-x86_64_wix\wixsample6\\test.wxs"
                                 " -sw5150 -gg -cg ProductComponents -srd -sfrag -dr INSTALLFOLDER -var var.PartsBuildDir"
                                 
                                 )

candle_action = SCons.Action.Action(
                                    "candle  -dPartsBuildDir=.\\_build\\build_debug_win32-x86_64_wix ${TARGET.dir}\\test.wxs"
                                 )



# internal wix package builder...
api.register.add_builder('_heat',SCons.Builder.Builder(
                    action = heat_action,
                    source_factory = SCons.Node.FS.Dir,
                    source_scanner = SCons.Defaults.DirScanner,
                    suffix = '.wxs',
				    ))



# internal wix package builder...
api.register.add_builder('_candle',SCons.Builder.Builder(
                    action = candle_action,
                    source_factory = SCons.Node.FS.Dir,
                    source_scanner = SCons.Defaults.DirScanner,
                    suffix = '.wixobj',
				    ))


