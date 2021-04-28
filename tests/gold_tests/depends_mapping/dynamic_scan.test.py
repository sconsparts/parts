Test.Summary = '''
This test the core of the dynamic builder/scan logic
'''
Setup.Copy.FromDirectory('dyn.depends')

######################################################
# builder everything
Test.AddBuildRun('all', '--use-env')

# everything should be up-to-date
Test.AddUpdateCheck('all', '--use-env')

######################################################
# we want to change a file to make sure we can rebuild 
# and not crash
tr=Test.AddBuildRun('all', '--use-env')
# define file that exists
scons_file = tr.Disk.File("part3/sconstruct")
# append some text, default logic to write before
# we start is good enough for test
scons_file.WriteAppendOn(
    '''
    # some text was added
    '''
)

# everything should be up-to-date
Test.AddUpdateCheck('all', '--use-env')

# do it again just check the the update check works
# we want to change a file to make sure we can rebuild 
# and not crash
tr=Test.AddOutOfDateCheckSCons('all', '--use-env')
# define file that exists
scons_file = tr.Disk.File("part3/sconstruct")
# append some text, defaut logic to write before
# we start is good enough for test
scons_file.WriteAppendOn(
    '''
    # some text was added
    '''
)
Test.AddBuildRun('all', '--use-env')
# everything should be up-to-date
Test.AddUpdateCheck('all', '--use-env')

# do it again just check the the update check works
# this time we change a header file as this can cause
# extra actions to happen
tr=Test.AddOutOfDateCheckSCons('all', '--use-env')
# define file that exists
scons_file = tr.Disk.File("part3/print_msg1.h")
# append some text, defaut logic to write before
# we start is good enough for test
scons_file.WriteAppendOn(
    '''
    /* some text was added */
    '''
)
Test.AddBuildRun('all', '--use-env')
# everything should be up-to-date
# this can easily break and not be up to date 
# because some "sdk" files did not copy
Test.AddUpdateCheck('all', '--use-env')


######################################################
# builder everything again with -j values
Test.AddCleanRun()
Test.AddBuildRun('all', '--use-env -j4')

# everything should be up-to-date
Test.AddUpdateCheck('all', '--use-env -j4')

######################################################
# we want to change a file to make sure we can rebuild 
# and not crash
tr=Test.AddBuildRun('all', '--use-env -j4')
# define file that exists
scons_file = tr.Disk.File("part3/sconstruct")
# append some text, defaut logic to write before
# we start is good enough for test
scons_file.WriteAppendOn(
    '''
    # some text was added
    '''
)

# everything should be up-to-date
Test.AddUpdateCheck('all', '--use-env -j4')

# do it again just check the the update check works
# we want to change a file to make sure we can rebuild 
# and not crash
tr=Test.AddOutOfDateCheckSCons('all', '--use-env -j4')
# define file that exists
scons_file = tr.Disk.File("part3/sconstruct")
# append some text, defaut logic to write before
# we start is good enough for test
scons_file.WriteAppendOn(
    '''
    # some text was added
    '''
)
Test.AddBuildRun('all', '--use-env -j4')
# everything should be up-to-date
Test.AddUpdateCheck('all', '--use-env -j4')

# do it again just check the the update check works
# this time we change a header file as this can cause
# extra actions to happen
tr=Test.AddOutOfDateCheckSCons('all', '--use-env -j4')
# define file that exists
scons_file = tr.Disk.File("part3/print_msg1.h")
# append some text, defaut logic to write before
# we start is good enough for test
scons_file.WriteAppendOn(
    '''
    /* some text was added */
    '''
)
Test.AddBuildRun('all', '--use-env -j4')
# everything should be up-to-date
# this can easily break and not be up to date 
# because some "sdk" files did not copy
Test.AddUpdateCheck('all', '--use-env -j4')

