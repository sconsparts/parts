import unittest
from parts.version import *

class TestVersions(unittest.TestCase):

    def test_version_parse(self):
        '''Test various version declaration methods.'''
        ver = version('1.2.3')
        self.assertTrue(ver == '1.2.3')
        
        ver = version(1.2, 3)
        self.assertTrue(ver == '1.2.3')
        
        ver = version(1, 2.3)
        self.assertTrue(ver == '1.2.3')
        
        ver = version(1.2, '3')
        self.assertTrue(ver == '1.2.3')
        
        ver = version(ver)
        self.assertTrue(ver == '1.2.3')
        
        ver = version(1.2, 3, 'beta')
        self.assertTrue(ver == '1.2.3.beta')
        
        ver = version(1.2, '3beta')
        self.assertTrue(ver == '1.2.3beta')
        
        ver = version('1.2.3.4.5.6.7.8.9')
        self.assertTrue(ver > '1.2.3.4.5.6.7.8.8')
        
        ver = version('1.2.99999999999')
        self.assertTrue(ver < '1.2.9999999999999999')
        
    def test_version_empty(self):
        '''Test handling of empty/None version objects.'''
        ver1 = version(None)
        ver2 = version('')
        self.assertTrue(ver1 == ver2)
        
        ver3 = version(0.1)
        self.assertTrue(ver1 < ver3)
        self.assertTrue(ver2 < ver3)
        
    def test_version_major(self):
        '''Test version.major() returns first number.'''
        ver = version('1.2.3.4')
        self.assertTrue(ver.major() == '1')
        
    def test_version_Major(self):
        '''Test version.Major() returns first number as string.'''
        ver = version(1.2, 3.4)
        self.assertTrue(ver.Major() == '1')
        
    def test_version_minor(self):
        '''Test version.minor() returns second number.'''
        ver = version('1.2.3.4')
        self.assertTrue(ver.minor() == '2')
        
    def test_version_Minor(self):
        '''Test version.Minor() returns second number as string.'''
        ver = version(1.2, 3.4)
        self.assertTrue(ver.Minor() == '2')
        
    def test_version_revision(self):
        '''Test version.revision() returns third number.'''
        ver = version('1.2.3.4')
        self.assertTrue(ver.revision() == '3')
        
    def test_version_Revision(self):
        '''Test version.Revision() returns third number as string.'''
        ver = version(1.2, 3.4)
        self.assertTrue(ver.Revision() == '3')
        
    def test_version_short(self):
        '''Test splice returns the first two numbers.'''
        ver = version('1.2.3.4.5.6.7.8.9')
        self.assertTrue(ver[:2] == '1.2')
        
    def test_version_weights(self):
        '''Test weight adjustments.'''
        oldweights = version.weights.copy()
        version.weights.update({
            'a': -1,
            'b': -2,
        })
        
        ver1 = version('1.2a')
        ver2 = version('1.2b')
        
        version.weights = oldweights
        self.assertTrue(ver1 >= ver2)
        
    def test_version_compare_self(self):
        '''Test version comparison with itself.'''
        ver = version('1.2.3')
        self.assertTrue(ver == ver)
        self.assertFalse(ver != ver)
        self.assertTrue(ver <= ver)
        self.assertTrue(ver >= ver)
        self.assertFalse(ver < ver)
        self.assertFalse(ver > ver)
        
    def test_version_compare_equal(self):
        '''Test version comparison with equivalent version.'''
        ver1 = version('1')
        ver2 = version('1.0.0')
        self.assertTrue(ver1 == ver2)
        self.assertFalse(ver1 != ver2)
        self.assertTrue(ver1 <= ver2)
        self.assertTrue(ver1 >= ver2)
        self.assertFalse(ver1 < ver2)
        self.assertFalse(ver1 > ver2)
        
    def test_version_compare_greater(self):
        '''Test version comparison with greater version.'''
        ver1 = version('1.2.3')
        ver2 = version('1.2.4')
        self.assertFalse(ver1 == ver2)
        self.assertTrue(ver1 != ver2)
        self.assertTrue(ver1 <= ver2)
        self.assertFalse(ver1 >= ver2)
        self.assertTrue(ver1 < ver2)
        self.assertFalse(ver1 > ver2)
        
    def test_version_compare_lesser(self):
        '''Test version comparison with lesser version.'''
        ver1 = version('1.2.3')
        ver2 = version('1.2.2')
        self.assertFalse(ver1 == ver2)
        self.assertTrue(ver1 != ver2)
        self.assertFalse(ver1 <= ver2)
        self.assertTrue(ver1 >= ver2)
        self.assertFalse(ver1 < ver2)
        self.assertTrue(ver1 > ver2)
        
    def test_version_compare_special(self):
        '''Test version comparison with special strings.'''
        ver1 = version('1.2.3')
        ver2 = version('1.2.3beta')
        self.assertFalse(ver1 == ver2)
        self.assertTrue(ver1 != ver2)
        self.assertFalse(ver1 <= ver2)
        self.assertTrue(ver1 >= ver2)
        self.assertFalse(ver1 < ver2)
        self.assertTrue(ver1 > ver2)
        
    def test_version_compare_special_both(self):
        '''Test version comparison where both have special strings.'''
        ver1 = version('1.2.3alpha')
        ver2 = version('1.2.3beta')
        self.assertFalse(ver1 == ver2)
        self.assertTrue(ver1 != ver2)
        self.assertTrue(ver1 <= ver2)
        self.assertFalse(ver1 >= ver2)
        self.assertTrue(ver1 < ver2)
        self.assertFalse(ver1 > ver2)
        
    def test_version_compare_special_long(self):
        '''Test version comparison with many subparts including specials.'''
        ver1 = version('1.2.3beta1rc5')
        ver2 = version('1.2.3beta1')
        self.assertFalse(ver1 == ver2)
        self.assertTrue(ver1 != ver2)
        self.assertTrue(ver1 <= ver2)
        self.assertFalse(ver1 >= ver2)
        self.assertTrue(ver1 < ver2)
        self.assertFalse(ver1 > ver2)
        
    def test_version_compare_char(self):
        '''Test version comparison including characters.'''
        ver1 = version('1.2.3b')
        ver2 = version('1.2.3')
        self.assertFalse(ver1 == ver2)
        self.assertTrue(ver1 != ver2)
        self.assertFalse(ver1 <= ver2)
        self.assertTrue(ver1 >= ver2)
        self.assertFalse(ver1 < ver2)
        self.assertTrue(ver1 > ver2)
        
    def test_version_compare_char_both(self):
        '''Test version comparison where both have characters.'''
        ver1 = version('1.2.3b')
        ver2 = version('1.2.3a')
        self.assertFalse(ver1 == ver2)
        self.assertTrue(ver1 != ver2)
        self.assertFalse(ver1 <= ver2)
        self.assertTrue(ver1 >= ver2)
        self.assertFalse(ver1 < ver2)
        self.assertTrue(ver1 > ver2)
                
    def test_version_compare_string(self):
        '''Test version comparison with strings.'''
        ver = version('1.2.3')
        self.assertTrue(ver == '1.2.3')
        self.assertTrue('1.3' != ver)
        self.assertTrue('1.1' <= ver)
        self.assertTrue('2.0' >= ver)
        self.assertTrue(ver < '3.2')
        self.assertTrue(ver > '0.1')
        
    def test_version_compare_char_both_with_string(self):
        '''Test version comparison where both have characters and one is a raw srting'''
        ver1 = version('1.2.3b')
        ver2 = '1.2.3a'
        self.assertFalse(ver1 == ver2)
        self.assertTrue(ver1 != ver2)
        self.assertFalse(ver1 <= ver2)
        self.assertTrue(ver1 >= ver2)
        self.assertFalse(ver1 < ver2)
        self.assertTrue(ver1 > ver2)
        
    def test_version_compare_special_both_with_string(self):
        '''Test version comparison where both have special strings and one is a raw srting.'''
        ver1 = version('1.2.3alpha')
        ver2 = '1.2.3beta'
        self.assertFalse(ver1 == ver2)
        self.assertTrue(ver1 != ver2)
        self.assertTrue(ver1 <= ver2)
        self.assertFalse(ver1 >= ver2)
        self.assertTrue(ver1 < ver2)
        self.assertFalse(ver1 > ver2)
        
    def test_version_compare_special_long_with_string(self):
        '''Test version comparison with many subparts including specials and one is a raw srting.'''
        ver1 = version('1.2.3beta1rc5')
        ver2 = '1.2.3beta1'
        self.assertFalse(ver1 == ver2)
        self.assertTrue(ver1 != ver2)
        self.assertTrue(ver1 <= ver2)
        self.assertFalse(ver1 >= ver2)
        self.assertTrue(ver1 < ver2)
        self.assertFalse(ver1 > ver2)

    def test_version_none(self):
        ''' Test version 0.0.0 is None'''
        ver1 = version('0.0.0')
        self.assertTrue(ver1 == None)
        self.assertFalse(ver1 != None)
        self.assertTrue(ver1 <= None)
        self.assertTrue(ver1 >= None)
        self.assertFalse(ver1 < None)
        self.assertFalse(ver1 > None)
        ver1 = version('0')
        self.assertTrue(ver1 == None)
        self.assertFalse(ver1 != None)
        self.assertTrue(ver1 <= None)
        self.assertTrue(ver1 >= None)
        self.assertFalse(ver1 < None)
        self.assertFalse(ver1 > None)


    def test_version_none2(self):
        ''' Test version() is None'''
        ver1 = version()
        self.assertTrue(ver1 == None)
        self.assertFalse(ver1 != None)
        self.assertTrue(ver1 <= None)
        self.assertTrue(ver1 >= None)
        self.assertFalse(ver1 < None)
        self.assertFalse(ver1 > None)

        
