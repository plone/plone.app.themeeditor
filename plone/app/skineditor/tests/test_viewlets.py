import unittest
import zope.component.testing
from zope.component import provideAdapter
from zope.app.component.hooks import setSite, setHooks
from zope.component.registry import Components
from zope.interface import Interface, implements
from zope.publisher.interfaces import IView
from zope.publisher.interfaces.browser import IBrowserRequest

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from five.customerize.zpt import TTWViewTemplate
from plone.app.customerize.tool import ViewTemplateContainer
from plone.app.skineditor.viewlet import ViewletResourceType
from zope.viewlet.interfaces import IViewlet, IViewletManager
from zope.viewlet.viewlet import ViewletBase
#from plone.app.viewletmanager.manager import OrderedViewletManager

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

class IDummyViewletManager(IViewletManager):
    pass

class SimpleViewlet(ViewletBase):
    index = ViewPageTemplateFile('cmf_test_skins/test/test.pt')

class ViewletResourceTestLayer:
    
    @classmethod
    def setUp(self):
        # global view registration
        provideAdapter(SimpleViewlet,
                       (Interface, IBrowserRequest, IView, IDummyViewletManager),
                       provides=IViewlet, name='viewlet')
        provideAdapter(SimpleViewlet,
                       (Interface, IDummyBrowserLayer, IView, IDummyViewletManager),
                       provides=IViewlet, name='viewlet')
        # local view registration
        site = DummySite()
        setSite(site)
        setHooks()
        custom_zpt = TTWViewTemplate(
            id = 'customized_viewlet',
            text = 'test',
            view = SimpleViewlet,
            permission = 'View',
            name = 'viewlet')
        site.portal_view_customizations.addTemplate('customized_viewlet', custom_zpt)
        sm = site.getSiteManager()
        sm.registerAdapter(custom_zpt,
                           (Interface, IDummyBrowserLayer, IView, IDummyViewletManager),
                           provided=IViewlet, name='viewlet')

    @classmethod
    def tearDown(self):
        zope.component.testing.tearDown()


class TestViewletResourceType(unittest.TestCase):
    layer = ViewletResourceTestLayer

    def setUp(self):
        self.rt = ViewletResourceType()

    def test_resource_order_and_attributes(self):
        resources = list(self.rt)
        self.assertEqual(len(resources), 3)
        
        # first resource: local registration, specific browser layer
        res = resources[0]
        self.assertEqual(res.name, 'viewlet')
        self.assertEqual(res.type, 'viewlet')
        self.assertEqual(res.description, 'Viewlet for * in the plone.app.skineditor.tests.test_viewlets.IDummyViewletManager manager')
        self.assertEqual(res.info, 'In the database: portal_view_customizations/customized_viewlet')
        self.assertEqual(res.context, ('zope.interface.Interface', 'plone.app.skineditor.tests.test_viewlets.IDummyViewletManager'))
        self.assertEqual(res.layer, 'plone.app.skineditor.tests.test_viewlets.IDummyBrowserLayer')
        self.assertEqual(res.actions, [('Edit', 'customized_viewlet/manage_main'),
                                       ('Remove', '/manage_delObjects?ids=customized_viewlet')])

        # second resource: global registration, specific browser layer
        res = resources[1]
        self.assertEqual(res.name, 'viewlet')
        self.assertEqual(res.type, 'viewlet')
        self.assertEqual(res.description, 'Viewlet for * in the plone.app.skineditor.tests.test_viewlets.IDummyViewletManager manager')
        self.failUnless(res.info.startswith('On the filesystem: '))
        self.failUnless(res.info.endswith('cmf_test_skins/test/test.pt'))
        self.assertEqual(res.context, ('zope.interface.Interface', 'plone.app.skineditor.tests.test_viewlets.IDummyViewletManager'))
        self.assertEqual(res.layer, 'plone.app.skineditor.tests.test_viewlets.IDummyBrowserLayer')
        self.assertEqual(res.actions, [('View', '/@@customizezpt.html?required=zope.interface.Interface,plone.app.skineditor.tests.test_viewlets.IDummyBrowserLayer,zope.browser.interfaces.IView,plone.app.skineditor.tests.test_viewlets.IDummyViewletManager&view_name=viewlet')])

        # third resource: global registration, general browser layer
        res = resources[2]
        self.assertEqual(res.name, 'viewlet')
        self.assertEqual(res.type, 'viewlet')
        self.assertEqual(res.description, 'Viewlet for * in the plone.app.skineditor.tests.test_viewlets.IDummyViewletManager manager')
        self.failUnless(res.info.startswith('On the filesystem: '))
        self.failUnless(res.info.endswith('cmf_test_skins/test/test.pt'))
        self.assertEqual(res.context, ('zope.interface.Interface', 'plone.app.skineditor.tests.test_viewlets.IDummyViewletManager'))
        self.assertEqual(res.layer, 'zope.publisher.interfaces.browser.IBrowserRequest')
        self.assertEqual(res.actions, [('View', '/@@customizezpt.html?required=zope.interface.Interface,zope.publisher.interfaces.browser.IBrowserRequest,zope.browser.interfaces.IView,plone.app.skineditor.tests.test_viewlets.IDummyViewletManager&view_name=viewlet')])

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
