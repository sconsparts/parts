

import ctypes
from builtins import range
from ctypes import windll

# From winerror.h

#
# MessageId: ERROR_MORE_DATA
#
# MessageText:
#
#  More data is available.
#
ERROR_MORE_DATA = 234    # dderror

#
# MessageId: ERROR_NO_MORE_ITEMS
#
# MessageText:
#
#  No more data is available.
#
ERROR_NO_MORE_ITEMS = 259


# From Msi.h
# typedef enum tagINSTALLSTATE
# {
INSTALLSTATE_NOTUSED = -7  # component disabled
INSTALLSTATE_BADCONFIG = -6  # configuration data corrupt
INSTALLSTATE_INCOMPLETE = -5  # installation suspended or in progress
INSTALLSTATE_SOURCEABSENT = -4  # run from source, source is unavailable
INSTALLSTATE_MOREDATA = -3  # return buffer overflow
INSTALLSTATE_INVALIDARG = -2  # invalid function argument
INSTALLSTATE_UNKNOWN = -1  # unrecognized product or feature
INSTALLSTATE_BROKEN = 0  # broken
INSTALLSTATE_ADVERTISED = 1  # advertised feature
INSTALLSTATE_REMOVED = 1  # component being removed (action state, not settable)
INSTALLSTATE_ABSENT = 2  # uninstalled (or action state absent but clients remain)
INSTALLSTATE_LOCAL = 3  # installed on local drive
INSTALLSTATE_SOURCE = 4  # run from source, CD or net
INSTALLSTATE_DEFAULT = 5  # use default, local or source
# } INSTALLSTATE;

# From MsiQuery.h
MSIDBOPEN_READONLY = 0  # database open read-only, no persistent changes
MSIDBOPEN_TRANSACT = 1  # database read/write in transaction mode
MSIDBOPEN_DIRECT = 2  # database direct read/write without transaction
MSIDBOPEN_CREATE = 3  # create new database, transact mode read/write
MSIDBOPEN_CREATEDIRECT = 4  # create new database, direct mode read/write
MSIDBOPEN_PATCHFILE = 16  # add flag to indicate patch file


class Product(object):

    def __init__(self, productGuid):
        self.__productGuid = productGuid

    def __getattr__(self, name):
        name = str(name)

        # Determine buffer size for data
        buffSize = ctypes.c_int(0)
        if windll.msi.MsiGetProductInfoW(self.__productGuid, name, None, ctypes.byref(buffSize)):
            raise AttributeError("Product '%s' has no '%s' attribute" % (str(self.__productGuid), name))

        # Allocate buffer for result
        buffSize = ctypes.c_int(buffSize.value + 1)
        resultBuffer = ctypes.create_unicode_buffer(buffSize.value)
        if windll.msi.MsiGetProductInfoW(self.__productGuid, name, resultBuffer, ctypes.byref(buffSize)):
            raise AttributeError("Product '%s' has no '%s' attribute" % (str(self.__productGuid), name))

        return resultBuffer.value

    def getComponentPath(self, component):
        buffSize = ctypes.c_int(0)
        ret = windll.msi.MsiGetComponentPathW(self.__productGuid, component, None, ctypes.byref(buffSize))
        if buffSize.value == 0:
            return ret, ""
        buffSize = ctypes.c_int(buffSize.value + 1)
        buff = ctypes.create_unicode_buffer(buffSize.value)

        ret == windll.msi.MsiGetComponentPathW(self.__productGuid, component, buff, ctypes.byref(buffSize))

        return ret, buff.value

    @property
    def ProductGuid(self):
        return self.__productGuid


class MsiHandle(object):

    def __init__(self, handle=None):
        self._handle = handle

    def __del__(self):
        if self._handle is not None:
            windll.msi.MsiCloseHandle(self._handle)

    def _check(self):
        if self._handle is None:
            raise ValueError("%s handle is None" % self.__class__.__name__)


class Database(MsiHandle):

    def __init__(self, path, persist):
        MsiHandle.__init__(self)
        handle = ctypes.c_int(0)
        ret = windll.msi.MsiOpenDatabaseW(path, persist, ctypes.byref(handle))
        if ret != 0:
            raise ctypes.WinError(ret)
        self._handle = handle

    def openView(self, query):
        self._check()
        query = str(query)
        viewHandle = ctypes.c_int(0)
        ret = windll.msi.MsiDatabaseOpenViewW(self._handle, query, ctypes.byref(viewHandle))
        if ret != 0:
            raise ctypes.WinError(ret)

        return View(viewHandle)


class View(MsiHandle):

    def getFieldNames(self):
        self._check()

        record = ctypes.c_int(0)

        ret = windll.msi.MsiViewGetColumnInfo(self._handle, 0, ctypes.byref(record))
        if ret != 0:
            raise ctypes.WinError(ret)

        return Record(record)

    def __iter__(self):
        self._check()

        hrec = ctypes.c_int(0)
        ret = windll.msi.MsiViewExecute(self._handle, hrec)
        if ret != 0:
            raise ctypes.WinError(ret)

        while True:
            hrec = ctypes.c_int(0)
            ret = windll.msi.MsiViewFetch(self._handle, ctypes.byref(hrec))
            if ret == 0:
                yield Record(hrec)
            elif ret != ERROR_NO_MORE_ITEMS:
                raise ctypes.WinError(ret)
            else:
                break


class Record(MsiHandle):

    def getFieldCount(self):
        self._check()
        try:
            return self.__fieldCount
        except AttributeError:
            if self._handle is None:
                raise ValueError("Record handle is None")
            self.__fieldCount = windll.msi.MsiRecordGetFieldCount(self._handle)
            return self.__fieldCount

    def valueAsString(self, index):
        self._check()

        tmp = ctypes.c_int16(0)
        charCount = ctypes.c_int(1)
        ret = windll.msi.MsiRecordGetStringW(self._handle, index, ctypes.byref(tmp), ctypes.byref(charCount))
        if ret == 0:
            return ""
        elif ret != ERROR_MORE_DATA:
            raise ctypes.WinError(ret)

        charCount = ctypes.c_int(charCount.value + 1)
        buff = ctypes.create_unicode_buffer(charCount.value)
        ret = windll.msi.MsiRecordGetStringW(self._handle, index, buff, ctypes.byref(charCount))
        if ret != 0:
            raise ctypes.WinError(ret)

        return buff.value

    def __iter__(self):
        for index in range(1, self.getFieldCount() + 1):
            yield self.valueAsString(index)


def allProducts():
    """
    Return all products known to MSI on the machine.
    """
    index = 0

    # Allocate big enough buffer to keep GUID plus null terminator
    buff = ctypes.create_unicode_buffer(len('{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}') + 1)
    while 0 == windll.msi.MsiEnumProductsW(index, buff):
        index += 1
        yield Product(buff.value)


if __name__ == '__main__':
    import re
    for product in allProducts():
        print('\t'.join(((product.ProductName or
                          product.ProductGuid).encode('mbcs', errors='ignore'),
                         getattr(product, 'VersionString',
                                 'No version info').encode('mbcs', errors='ignore'))))
# vim: set et ts=4 sw=4 ft=python :
