# this is the Console Application form of the gtest (gold test) package
import sys
import os
from copy import copy
from functools import partial
import optparse

import gtest.engine
import gtest.hosts
import gtest.setuptasks

class MyOption(optparse.Option):
    @staticmethod
    def checkPath(cls, opt, value, shouldExist=True):
        path = os.path.abspath(value)
        if shouldExist and not os.path.exists(path):
            raise optparse.OptionValueError('%s is not a valid path needed for option %s' % \
                                            (value, opt))
        return path

    @staticmethod
    def checkJobValue(cls, opt, value):
        try:
            amount = int(value)
        except ValueError:
            raise optparse.OptionValueError('%s should have integer value, got %s instead' % \
                                            (opt, value))
        if amount < 0:
            raise optparse.OptionValueError('%s should not be negative (got %s)' % \
                                            (opt, value))
        return amount or 1
    
    TYPES = optparse.Option.TYPES + ('existing_abspath', 'abspath', 'job_amount')
    TYPE_CHECKER = copy(optparse.Option.TYPE_CHECKER)
    
    def __init__(self, *args, **kw):
        optparse.Option.__init__(self, *args, **kw)
        MyOption.TYPE_CHECKER['existing_abspath'] = MyOption.checkPath
        MyOption.TYPE_CHECKER['abspath'] = partial(MyOption.checkPath, shouldExist=False)
        MyOption.TYPE_CHECKER['job_amount'] = MyOption.checkJobValue
    
if __name__ == '__main__':
    # create primary commandline parser
    parser = optparse.OptionParser(option_class=MyOption, version='%prog 1.0.Beta')

    parser.add_option("-D", "--directory", type='existing_abspath', dest='directory',
                      default=os.path.abspath('.'),
                      help="The directory with all the tests in them")
    parser.add_option("--gtest-site", type='existing_abspath', dest='gtest_site',
                      help="A user provided gtest-site directory to use instead of the default")
    parser.add_option("--sandbox", type='abspath', default=os.path.abspath('./_sandbox'),
                      dest='sandbox', help="The root directory in which the tests will be run")
    parser.add_option("-j", "--jobs", default=1, type='job_amount', dest='job_amount',
                      help="The number of tests to try to run at the same time")
    parser.add_option("-f", "--filter-in", default="*", dest='filter_in',
                      help="Filter-in the tests by their names")
    parser.add_option("--dump-report", default=False, action='store_true', dest='dump_report',
                      help='Enable dumping the run report in JSON format to stdout')
    
    # this is a commandline tool so make the cli host
    MyHost = gtest.hosts.ConsoleHost(parser)

    #parser should have all option defined by program and or host type defined
    options, args = parser.parse_args()

    # this is a cli program so we only make one engine and run it
    # a GUI might make a new GUI for every run as it might have new options, or maybe not
    myEngine = gtest.Engine(MyHost, jobs=options.job_amount, test_dir=options.directory,
                            run_dir=options.sandbox, gtest_site=options.gtest_site,
                            filter_in=options.filter_in, dump_report=options.dump_report)

    ret = myEngine.Start()
    exit(ret)

# vim: set et ts=4 sw=4 ai :

