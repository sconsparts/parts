'''
this file contains pattern which is used to select file on disk based on simple
matching expressions. Scons just add a Glob function.. need to consider using that
internal here instead, and then possiblely removing pattern 100%
'''

## patterns
import common
import api

import SCons.Script

from SCons.Debug import logInstanceCreation

import os

def pattern(env,sub_dir='' ,src_dir  = '', includes = ['*'], excludes = [],recursive=True):
    return Pattern(sub_dir,src_dir, includes, excludes,recursive)

g_db={}

class Pattern(object):
    def __init__(self,sub_dir='' ,src_dir  = '', includes = ['*'], excludes = [],recursive=True):
        if __debug__: logInstanceCreation(self)
        self.sub_dir=sub_dir
        self.src_dir=SCons.Script.Dir(SCons.Script.Dir('.').srcnode().Dir(src_dir).abspath)

        #print "Pattern src_dir (srcnode):",self.src_dir.srcnode().abspath
        #print "Pattern src_dir path     :",self.src_dir.abspath
        self.includes=[]
        for i in includes:
            self.includes.append(os.path.normpath(i))
        #self.includes=includes
        self.excludes=[]
        for i in excludes:
            if i != '*':
                self.excludes.append(os.path.normpath(i))
        #self.excludes=excludes
        self.recursive=recursive
        self.map=None

    def sub_dirs(self):
        if self.map==None:
            self.generate()
        return self.map.keys()

    def files(self,directory=None):
        ''' basicly do a recursive glob '''
        if self.map is None:
            self.generate()
        if directory is None:
            fl=[]
            #root_path=SCons.Script.Dir('.').srcnode().abspath
            root_path=SCons.Script.Dir('.').srcnode().abspath
            if self.src_dir.abspath.startswith(root_path) == False:
                root_path=self.src_dir.abspath
            for k,v in self.map.iteritems():
                for f in v:
                    s=common.relpath(os.path.join(k,f),root_path)
                    fl.append(s)

            return fl

        return self.map[directory]

    def target_source(self,root_target):

        src_list=[]
        trg_list=[]
        if self.map is None:
            self.generate()
        for k,v in self.map.iteritems():
            final_path=os.path.join(root_target,k)
            for f in v:
                trg_list.append(os.path.join(final_path,os.path.split(f)[1]))
                src_list.append(f)

        return (trg_list,src_list)

    ### code that originally updated the install tree,
    ### but refactored to be more python like.
    ### made a matches function that is used in the logic below
    def generate(self,exclude_path=''):
        global g_db
        m = {}
       # create base path
        base_path=self.src_dir.abspath
        l=len(base_path)
        # make list of paths to search
        paths=[base_path]
        for path in paths:

            #for this path get the list of item in it
##            try:
##                # try to see if we had scanned this already
##                files=g_db[path]

##                for f in files:
##                    if common.is_list(f):
##                        currpath = os.path.join(path,f[0])
##                        paths.append(currpath)
##                        continue
##                    currpath = os.path.join(path,f)
##
##                    if common.matches(currpath[l+1:], self.includes, self.excludes):
##                        key=os.path.join(self.sub_dir,path[l+1:])
##                        try:
##                            m[key].append(currpath)
##                        except KeyError:
##                            m[key]=[currpath]
##            except KeyError:

                g_db[path]=[]
                # don't have it.. so make the chache and do the search
                for file in os.listdir(path):
                    # combine the path and the file
                    currpath = os.path.join(path,file)

                    key=os.path.join(self.sub_dir,path[l+1:])

                    # see if this is really a path
                    is_dir=os.path.isdir(currpath)
                    if is_dir and self.recursive and file[0]!='.':
                        tmp=os.path.split(currpath)
                        g_db[tmp[0]].append([tmp[1]])
                        # if so and we want to recurse, add to paths list
                        el=len(exclude_path) # should make exclude path a list??
                        if currpath[:el]!=exclude_path or el==0:
                            paths.append(currpath)
                    elif is_dir == False and common.matches(currpath[l+1:], self.includes, self.excludes):
                        # else see if it matches pattern and store if it does
                        tmp=os.path.split(currpath)
                        try:
                            m[key].append(currpath)
                        except KeyError:
                            m[key]=[currpath]
                        g_db[tmp[0]].append(tmp[1])
                    else:

                        tmp=os.path.split(currpath)
                        g_db[tmp[0]].append(tmp[1])


                #else we ignore the item
        self.map=m





# This is what we want to be setup in parts
from SCons.Script.SConscript import SConsEnvironment

# adding logic to Scons Enviroment object
SConsEnvironment.Pattern=pattern

api.register.add_global_object('Pattern',Pattern)
api.register.add_global_parts_object('Pattern',Pattern)
