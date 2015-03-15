
import gtest.setup
import os

class CreateRepository(gtest.setup.SetupTask):
    def __init__(self,name):#,dir_to_add):
        self._name=name
        #self._dir_to_add=dir_to_add
        super(CreateRepository, self).__init__(
                    taskname="Create SVN repository"
                    )
        

    def setup(self):
        repo_path = os.path.abspath(os.path.join(self.SandBoxDir, self._name)).replace('\\', '/')
        self.Env['{0}_SVN_PATH'.format(self._name.upper())]="file://localhost/"+repo_path

        if os.path.exists(repo_path):
            raise gtest.setup.Error('Repository at "%s" already exists' % repo_path)

        # create Repo
        cmd_str= 'svnadmin create "{0}"'.format(repo_path)
        if self.RunCommand(cmd_str):
            raise gtest.setup.Error('Setup command "{0}" Failed'.format(cmd_str))

    def cleanup(self):
        pass


class ImportDirectory(gtest.setup.SetupTask):
    def __init__(self,name,dir_to_add, sub_dir=''):
        self._name=name
        self._dir_to_add=dir_to_add
        self._sub_dir=sub_dir
        super(ImportDirectory, self).__init__(
                    taskname="Import SVN repository"
                    )
        

    def setup(self):
        path_to_add = os.path.abspath(os.path.join(self.TestFileDir, self._dir_to_add))
        try:
            repo_path=self.Env['{0}_SVN_PATH'.format(self._name.upper())]
        except:
            # error if we don't have a value for this.. meaning they did not create or define a repository
            raise gtest.setup.Error('SVN repository "{}" does not exist for importing'.format(self.name))
        
        repo_path+="/"+self._sub_dir
        # add directory
        cmd_str = 'svn import "{0}" "{1}" -m "" --non-interactive'.format(path_to_add, repo_path)
        if self.RunCommand(cmd_str):
            raise gtest.setup.Error('Setup command "{0}" Failed'.format(cmd_str))

    def cleanup(self):
        pass


#class CheckOut(gtest.setup.SetupTask):
#class DefineRepository(gtest.setup.SetupTask):



gtest.setup.AddSetupTask(CreateRepository,ns="Svn")
gtest.setup.AddSetupTask(ImportDirectory,ns="Svn")
