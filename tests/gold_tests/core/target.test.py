Test.Summary='''
This is a test to see if the different targets work as expected. For this work we have to have correct alias generation.
'''
Setup.Copy.FromDirectory('target_test')

t=Test.AddBuildRun("print_msg@version:1",'INSTALL_LIB=#install')
t.Disk.File("install/print_msg_1.0.0.txt",exists=True)

t=Test.AddBuildRun("print_msg@version:2",'INSTALL_LIB=#install')
t.Disk.File("install/print_msg_2.0.0.txt",exists=True)
