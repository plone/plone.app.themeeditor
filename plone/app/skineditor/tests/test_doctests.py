from unittest import TestSuite
from doctest import ELLIPSIS
from Testing.ZopeTestCase import ZopeTestCase, ZopeDocTestSuite

test_zope_modules = ('plone.app.skineditor.zopeview',)
optionflags = ELLIPSIS

def test_suite():
    suite = TestSuite()
    suite.addTests([ZopeDocTestSuite(m, optionflags=optionflags, test_class=ZopeTestCase)
        for m in test_zope_modules])
    return suite
