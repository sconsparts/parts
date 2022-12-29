Test.Summary = '''
This test checks that Extract works correctly
'''
Setup.Copy.FromDirectory('extract3')
Setup.Copy("testdata.zip")

t = Test.AddBuildRun('all','BUILD_DIR="#build" mode=zip')
t.ReturnCode = 0

# test for some basic files
t.Disk.File("build/extracted/sconstruct").Exists=True
t.Disk.File("build/extracted/engine/include/core.h").Exists=False
t.Disk.File("build/extracted/engine/common/common.cpp").Exists=True
t.Disk.File("build/extracted/engine/core/core.cpp").Exists=True
t.Disk.File("build/extracted/engine/utest2/test.cpp").Exists=True
t.Disk.File("build/extracted/engine/common/common.parts").Exists=False
t.Disk.File("build/extracted/engine/core/core.parts").Exists=True
t.Disk.File("build/extracted/engine/utest/unit_test.part").Exists=False
