import unittest
import zope.component.testing
from zope.component import provideAdapter
from zope.app.component.hooks import setSite
from zope.component.registry import Components
from zope.interface import Interface, implements
from zope.publisher.interfaces.browser import IBrowserRequest

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.customerize.tool import ViewTemplateContainer
from plone.app.skineditor.zopeview import ZopeViewResourceType

class DummyRequest(object):
    implements(IBrowserRequest)

class DummySite(object):
    REQUEST = DummyRequest()
    def __init__(self):
        self.registry = Components('components')
        self.portal_view_customizations = ViewTemplateContainer()
    def getSiteManager(self):
        return self.registry

class SimpleViewClass(BrowserView):
    index = ViewPageTemplateFile('cmf_test_skins/test/test.pt')

class ZopeViewResourceTestLayer:
    
    @classmethod
    def setUp(self):
        # global view registration
        provideAdapter(SimpleViewClass, (Interface, IBrowserRequest), provides=Interface, name='view')
        # local view registration
        site = DummySite()
        setSite(site)
        sm = site.getSiteManager()
        sm.registerAdapter(SimpleViewClass, (Interface, IBrowserRequest), provided=Interface, name='view')

    @classmethod
    def tearDown(self):
        zope.component.testing.tearDown()


class TestZopeViewResourceType(unittest.TestCase):
    layer = ZopeViewResourceTestLayer

    def setUp(self):
        self.rt = ZopeViewResourceType()

    def test_iter(self):
        resources = list(self.rt)
        self.assertEqual(len(resources), 2)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
