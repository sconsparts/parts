# There are for internal usage and should not be used by the users of Parts


import atexit
import functools


class classproperty:
    """
    Decorator that the make a class level property. By design it is read only
    """
    def __init__(self, method=None):
        self.classmethod = method

    def __get__(self, instance, cls=None):
        return self.classmethod(cls)

    def getter(self, method):
        self.classmethod = method
        return self

def overrideFunction(parent, functionName, returnOriginal=False):
    '''
    The decorator to ease overriding functions in a module or methods in a class.

    Wrapped function can access original function as its __original__ attribute, e.g.
        @overrideFunction(module, 'func1')
        def myfunc(someArgs):
            # doSomething
            return myfunc.__original__(someArgs)

    One could set returnOriginal to True to make that return statement be done in the decorator
    '''

    def wrapper(func):
        '''
        The wrapper that generates replacement function and replaces parent's functionName
        with it
        '''
        originalFunction = getattr(parent, functionName)
        if returnOriginal:
            def replacement(*args, **kw):
                '''
                The function that does calling the patch and calls original function after that
                '''
                func(*args, **kw)
                return originalFunction(*args, **kw)
        else:
            # if we're not requested to call original function optimize for speed - don't do
            # one extra nested call, just use "func" as replacement
            replacement = func

        replacement.__original__ = originalFunction
        functools.update_wrapper(replacement, originalFunction)
        setattr(parent, functionName, replacement)
        return replacement
    return wrapper


def onPythonExit(func):
    '''
    Execute the func at interpreter exit
    '''
    atexit.register(func)
    return func
