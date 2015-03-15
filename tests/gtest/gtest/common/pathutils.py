import stat
import os
import shutil

def remove_read_only(func, path, exc_info):
    """
    common helper function for shutil functions.
    This will try to see if the file we failed to remove
    was due to lack of write access ( 

    Usage : ``shutil.rmtree(path, onerror=remove_read_only)``
    """
    
    # Is the error an write access error 
    # ie write (implies delete permissions on windows) 
    # are needed to remove a file
    if not os.access(path, os.W_OK):
        # this file does not have write 
        # so set write permission
        os.chmod(path, stat.S_IWUSR)
        # reapply the function
        func(path)
    else:
        #This failed for a different reason
        raise


def gen_tree_action(src,dest,func):

    #get list files in src area
    files=os.listdir(src)
    for x in files:
        fullsrc=os.path.join(src, x)
        fulldest=os.path.join(dest, x)
        if os.path.isfile(fullsrc):
            func(fullsrc,dest)            
        elif os.path.isdir(fullsrc):
            gen_tree_action(fullsrc,fulldest,func)
            

def copy_tree(src,dest):
    '''does a copy of a files from directory in source to
    the directory dest. Makes directory if needed.
    This is different from shutil.copytree that errors out if the dest directory
    already exists
    '''
    def copyfunc(src,dest):
        if not os.path.exists(dest):
            os.makedirs(dest)
        shutil.copy2(src,dest)
    gen_tree_action(src,dest,copyfunc)

