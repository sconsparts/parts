
# simple event class
# need to look at extending this or 
# finding a usable existing solution



class Event(object):
    
    def __init__(self):
        self.__callbacks = set()

    def Connect(self, callback):
        self.__callbacks.add(callback)
        return self

    def __iadd__(self, callback):
        return self.Connect(callback)

    def Disconnect(self, callback):
        try:
            self.__callbacks.remove(callback)
        except:
            pass
        return self

    def __isub__(self, callback):
        return self.Disconnect(callback)    

    def __call__(self, *args, **kargs):   
        for callback in self.__callbacks:
            #print "  ",callback.Description
            callback(*args, **kargs)
            #print "  ",callback.Reason

    def __len__(self):
        return len(self.__callbacks)

    @property
    def Testers(self):
        return  self.__callbacks

