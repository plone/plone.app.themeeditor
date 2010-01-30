import unittest
import zope.component.testing
from zope.component import provideAdapter
from zope.app.component.hooks import setSite, setHooks
from zope.component.registry import Components
from zope.interface import Interface, implements
from zope.publisher.interfaces.browser import IBrowserRequest

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from five.customerize.zpt import TTWViewTemplate
from plone.app.customerize.tool import ViewTemplateContainer
from plone.app.skineditor.zopeview import ZopeViewResourceType

class IDummyBrowserLayer(IBrowserRequest):
    pass

class DummyRequest(object):
    implements(IDummyBrowserLayer)

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
        provideAdapter(SimpleViewClass, (Interface, IDummyBrowserLayer), provides=Interface, name='view')
        # local view registration
        site = DummySite()
        setSite(site)
        setHooks()
        custom_zpt = TTWViewTemplate(
            id = 'customized_view',
            text = 'test',
            view = SimpleViewClass,
            permission = 'View',
            name = 'view')
        site.portal_view_customizations.addTemplate('customized_view', custom_zpt)
        sm = site.getSiteManager()
        sm.registerAdapter(custom_zpt, (Interface, IDummyBrowserLayer), provided=Interface, name='view')

    @classmethod
    def tearDown(self):
        zope.component.testing.tearDown()


class TestZopeViewResourceType(unittest.TestCase):
    layer = ZopeViewResourceTestLayer

    def setUp(self):
        self.rt = ZopeViewResourceType()

    def test_resource_order_and_attributes(self):
        resources = list(self.rt)
        self.assertEqual(len(resources), 3)
        
        # first resource: local registration, specific browser layer
        res = resources[0]
        self.assertEqual(res.name, 'view')
        self.assertEqual(res.type, 'zopeview')
        self.assertEqual(res.description, 'View for *')
        self.assertEqual(res.info, 'In the database: portal_view_customizations/customized_view')
        self.assertEqual(res.context, 'zope.interface.Interface')
        self.assertEqual(res.layer, 'plone.app.skineditor.tests.test_zopeview.IDummyBrowserLayer')
        self.assertEqual(res.actions, [('Edit', 'customized_view/manage_main'),
                                       ('Remove', '/manage_delObjects?ids=customized_view')])

        # second resource: global registration, specific browser layer
        res = resources[1]
        self.assertEqual(res.name, 'view')
        self.assertEqual(res.type, 'zopeview')
        self.assertEqual(res.description, 'View for *')
        self.failUnless(res.info.startswith('On the filesystem: '))
        self.failUnless(res.info.endswith('cmf_test_skins/test/test.pt'))
        self.assertEqual(res.context, 'zope.interface.Interface')
        self.assertEqual(res.layer, 'plone.app.skineditor.tests.test_zopeview.IDummyBrowserLayer')
        self.assertEqual(res.actions, [('View', '/@@customizezpt.html?required=zope.interface.Interface,plone.app.skineditor.tests.test_zopeview.IDummyBrowserLayer&view_name=view')])

        # third resource: global registration, general browser layer
        res = resources[2]
        self.assertEqual(res.name, 'view')
        self.assertEqual(res.type, 'zopeview')
        self.assertEqual(res.description, 'View for *')
        self.failUnless(res.info.startswith('On the filesystem: '))
        self.failUnless(res.info.endswith('cmf_test_skins/test/test.pt'))
        self.assertEqual(res.context, 'zope.interface.Interface')
        self.assertEqual(res.layer, 'zope.publisher.interfaces.browser.IBrowserRequest')
        self.assertEqual(res.actions, [('View', '/@@customizezpt.html?required=zope.interface.Interface,zope.publisher.interfaces.browser.IBrowserRequest&view_name=view')])

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
