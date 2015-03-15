import sys
import os

def setupDefault():
    try:
        # In 1st turn use parts from current working directory. In 2nd turn
        # use parts installed into Python
        import parts.datacache
    except ImportError:
        try:
            partsLocalPath = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..'))
        except:
            partsLocalPath = '../'

        sys.path.append(partsLocalPath)
        if not 'PYTHONPATH' in os.environ:
            os.environ['PYTHONPATH'] = partsLocalPath
        else:
            os.environ['PYTHONPATH'] += os.pathsep + partsLocalPath

    import parts.pnode.pnode as parts_pnode_pnode
    def reprPnode(self):
        return "<{0} object ID={1}>".format(self.__class__.__name__,self.ID)
    parts_pnode_pnode.pnode.__repr__ = reprPnode
