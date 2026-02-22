"""Tests for parts.settings module.

Tests validation classes (All, OneOf, AnyOf) and default settings initialization.
"""
import pytest
from parts.settings import *


def _tester(item):
    """Test helper: returns True if item is a string."""
    return isinstance(item, str)


class TestSettings:
    """Test settings initialization and configuration."""

    def test_DefaultSettings_DefaultEnvironment(self):
        """Test that default environment can be created."""
        defEnv = DefaultSettings().DefaultEnvironment()
        # DefaultEnvironment returns an SCons environment object
        assert defEnv is not None

    def test_DefaultSettings_Environment(self):
        """Test that environment accepts custom variables."""
        env = DefaultSettings().Environment(name1='val1', name2='val2')
        assert env['name1'] == 'val1'
        assert env['name2'] == 'val2'


class TestAll:
    """Test All validation class."""

    def test_All_mixed(self):
        """Test All when some elements are valid (instances of str)."""
        someInst = All(1, '1', self, '', 0.1, str())
        assert someInst.Valid(_tester) is False
        assert someInst.GetValues() == (1, '1', self, '', 0.1, str())

    def test_All_valid(self):
        """Test All when all elements are valid (instances of str)."""
        allInst = All('1', '', str())
        assert allInst.Valid(_tester) is True
        assert allInst.GetValues() == ('1', '', str())

    def test_All_none_valid(self):
        """Test All when no elements are valid."""
        noneInst = All(1, self, 0.1)
        assert noneInst.Valid(_tester) is False
        assert noneInst.GetValues() == (1, self, 0.1)


class TestOneOf:
    """Test OneOf validation class."""

    def test_OneOf_mixed(self):
        """Test OneOf when some elements are valid."""
        someInst = OneOf(1, '1', self, '', 0.1, str())
        assert someInst.Valid(_tester) is True
        assert someInst.GetValues(_tester) == ['1']

    def test_OneOf_valid(self):
        """Test OneOf when all elements are valid."""
        allInst = OneOf('1', '', str())
        assert allInst.Valid(_tester) is True
        assert allInst.GetValues(_tester) == ['1']

    def test_OneOf_none_valid(self):
        """Test OneOf when no elements are valid."""
        noneInst = OneOf(1, self, 0.1)
        assert noneInst.Valid(_tester) is False
        assert noneInst.GetValues(_tester) == []


class TestAnyOf:
    """Test AnyOf validation class."""

    def test_AnyOf_mixed(self):
        """Test AnyOf when some elements are valid."""
        someInst = AnyOf(1, '1', self, '', 0.1, str())
        assert someInst.Valid(_tester) is True
        assert someInst.GetValues(_tester) == ['1', '', str()]

    def test_AnyOf_valid(self):
        """Test AnyOf when all elements are valid."""
        allInst = AnyOf('1', '', str())
        assert allInst.Valid(_tester) is True
        assert allInst.GetValues(_tester) == ['1', '', str()]

    def test_AnyOf_none_valid(self):
        """Test AnyOf when no elements are valid."""
        noneInst = AnyOf(1, self, 0.1)
        assert noneInst.Valid(_tester) is False
        assert noneInst.GetValues(_tester) == []

