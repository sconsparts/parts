Test.Summary = '''
This test checks that Extract works correctly
'''
Setup.Copy.FromDirectory('extract1')
Setup.Copy("testdata.tar.gz")

t = Test.AddBuildRun('all','BUILD_DIR="#build" mode=gz')
t.ReturnCode = 0

# test for some basic files
t.Disk.File("build/extracted/sconstruct").Exists=True
t.Disk.File("build/extracted/engine/include/core.h").Exists=True
t.Disk.File("build/extracted/engine/common/common.cpp").Exists=True
t.Disk.File("build/extracted/engine/core/core.cpp").Exists=True
t.Disk.File("build/extracted/engine/utest2/test.cpp").Exists=True

t.Disk.File("build/extracted2/sconstruct").Exists=True
t.Disk.File("build/extracted2/engine/include/core.h").Exists=True
t.Disk.File("build/extracted2/engine/common/common.cpp").Exists=True
t.Disk.File("build/extracted2/engine/core/core.cpp").Exists=True
t.Disk.File("build/extracted2/engine/utest2/test.cpp").Exists=True

t.Disk.File("build/extracted3/sconstruct").Exists=True
t.Disk.File("build/extracted3/engine/include/core.h").Exists=True
t.Disk.File("build/extracted3/engine/common/common.cpp").Exists=True
t.Disk.File("build/extracted3/engine/core/core.cpp").Exists=True
t.Disk.File("build/extracted3/engine/utest2/test.cpp").Exists=True

