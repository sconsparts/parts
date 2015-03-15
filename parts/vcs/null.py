from base import base

class null_t(base):
    """an empty vcs class, used when there is no vcs object for a part to use
    
    This basically allow the use of the VCS objet in a way that does not break any logic 
    expecting an vcs object. It will basically say it is always up to data.
    """
    __slots__=[]
    def __init__(self):
        super(null_t,self).__init__("","")

    def NeedsToUpdate(self):
        return False

    @property
    def _cache_filename(self):
        # Should be implemented in derived class
        return ''

    @base.CacheFileExists.getter
    def CacheFileExists(self):
        return True
    
null=null_t()
