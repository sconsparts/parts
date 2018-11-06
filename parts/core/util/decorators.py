# There are for internal usage and should not be used by the users of Parts
from __future__ import absolute_import, division, print_function

import atexit
import functools


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
