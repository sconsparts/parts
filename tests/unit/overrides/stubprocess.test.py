import sys
if sys.platform in ('linux2', 'darwin'):
    import subprocess
    import parts.overrides.stubprocess
    import unittest
    import os

    class TestMain(unittest.TestCase):
        def test_main(self):
            self.assertEqual(__file__, subprocess.Popen(['ls {0}'.format(__file__)],
                        shell=True, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE).communicate()[0].strip())

    class TestExcutableDoesNotExist(unittest.TestCase):
        def test_doesNotExist(self):
            def call_it():
                executable = 'does not exist'
                subprocess.Popen([executable], executable = executable).wait()
            self.assertRaises(OSError, call_it)

    class TestLongArguments(unittest.TestCase):
        def setUp(self):
            ARG_MAX = parts.overrides.stubprocess.ARG_MAX
            def cleanup():
                parts.overrides.stubprocess.ARG_MAX = ARG_MAX
            self.addCleanup(cleanup)
            parts.overrides.stubprocess.ARG_MAX = len(__file__)
        def test_longParams(self):
            self.assertEqual(__file__, subprocess.Popen(['ls {0}'.format(__file__)],
                        shell=True, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE).communicate()[0].strip())

    class TestEnvPassing(unittest.TestCase):
        def test_envPassing(self):
            self.assertEqual(__file__, subprocess.Popen(['ls {0}'.format(__file__)],
                        shell=True, stdout=subprocess.PIPE, env = os.environ,
                        stderr=subprocess.PIPE).communicate()[0].strip())
        def test_envPassed(self):
            self.assertEqual('PASSED', subprocess.Popen(['echo $PASSIT'],
                        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        env=dict(os.environ, PASSIT='PASSED')).communicate()[0].strip())
    class TestEnvIndirect(unittest.TestCase):
        def setUp(self):
            os_environ = os.environ
            def cleanup():
                os.environ = os_environ
            self.addCleanup(cleanup)
            os.environ = dict(os.environ)

        def test_envPassed(self):
            os.environ['PASSIT'] = 'PASSED'
            self.assertEqual('PASSED', subprocess.Popen(['echo $PASSIT'],
                        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                        ).communicate()[0].strip())


# vim: set et ts=4 sw=4 ai ft=python :

