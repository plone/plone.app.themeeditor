from unittest import TestSuite
from doctest import DocTestSuite, ELLIPSIS
from Testing.ZopeTestCase import ZopeTestCase, ZopeDocTestSuite
from Products.CMFTestCase.CMFTestCase import CMFTestCase
from Products.CMFTestCase.setup import setupCMFSite

test_modules = ('plone.app.skineditor.retriever',)
test_cmf_modules = ('plone.app.skineditor.cmf',)
test_zope_modules = ('plone.app.skineditor.zopeview',)
optionflags = ELLIPSIS

setupCMFSite()

def test_suite():
    suite = TestSuite()
    suite.addTests([DocTestSuite(m, optionflags=optionflags) for m in test_modules])
    suite.addTests([ZopeDocTestSuite(m, optionflags=optionflags, test_class=CMFTestCase)
        for m in test_cmf_modules])
    suite.addTests([ZopeDocTestSuite(m, optionflags=optionflags, test_class=ZopeTestCase)
        for m in test_zope_modules])
    return suite
