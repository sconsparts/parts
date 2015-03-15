import os

import gtest.setup

class Copy(gtest.setup.SetupTask):
    def __init__(self,source,target=None):
        super(Copy, self).__init__(
                    taskname="Copy"
                    )
        self.source=source
        self.target=target

    def setup(self):
        self.Copy(self.source,self.target)

class FromDirectory(gtest.setup.SetupTask):
    def __init__(self,source):
        super(FromDirectory, self).__init__(
                    taskname="Setup test from Directory"
                    )
        self.source=source

    def setup(self):
        self.Copy(self.source,self.SandBoxDir)

class FromTemplate(gtest.setup.SetupTask):
    def __init__(self,source):
        super(FromTemplate, self).__init__(
                    taskname="Setup test from Template"
                    )
        self.source=source

    def setup(self):
        self.Copy(os.path.join(self.TestRootDir,"templates",self.source),self.SandBoxDir)


gtest.setup.AddSetupTask(Copy,"__call__",ns='Copy')
gtest.setup.AddSetupTask(FromDirectory,ns='Copy')
gtest.setup.AddSetupTask(FromTemplate,ns='Copy')
