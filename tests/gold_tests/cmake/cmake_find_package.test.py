Test.Summary = '''
A consumer part's cmake build resolves find_package() for a provider part's
config via the CMAKE_PREFIX_PATH propagated by InstallCMakeConfig/SdkCMakeConfig.
'''

Test.SkipUnless(
    Condition.HasProgram('cmake', 'cmake is required to run this build'),
)

Setup.Copy.FromDirectory('cmake_find_package')

# find_package(foo REQUIRED) in the consumer's CMakeLists halts the build if the
# provider's config is not found, so a clean build proves the propagation chain.
t = Test.AddBuildRun('all')
t.ReturnCode = 0
