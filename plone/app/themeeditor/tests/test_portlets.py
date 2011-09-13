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
#from plone.app.themeeditor.viewlet import ViewletResourceType
from plone.app.themeeditor.portlet import PortletResourceType
#from zope.viewlet.interfaces import IViewlet, IViewletManager
#from zope.viewlet.viewlet import ViewletBase
from plone.portlets.interfaces import IPortletManager, IPortletRenderer
from plone.app.portlets.portlets.base import Renderer

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

class IDummyPortletManager(IPortletManager):
    pass

class DummyPortlet(Renderer):
    index = ViewPageTemplateFile('cmf_test_skins/test/test.pt')

class PortletResourceTestLayer:
    
    @classmethod
    def setUp(self):
        # global view registration
        provideAdapter(DummyPortlet,
                       (Interface, IBrowserRequest, IView, IDummyPortletManager, Interface),
                       provides=IPortletRenderer, name='portlet')
        provideAdapter(DummyPortlet,
                       (Interface, IDummyBrowserLayer, IView, IDummyPortletManager, Interface),
                       provides=IPortletRenderer, name='portlet')
        # local view registration
        site = DummySite()
        setSite(site)
        setHooks()
        custom_zpt = TTWViewTemplate(
            id = 'customized_portlet',
            text = 'test',
            view = DummyPortlet,
            permission = 'View',
            name = 'portlet')
        site.portal_view_customizations.addTemplate('customized_portlet', custom_zpt)
        sm = site.getSiteManager()
        sm.registerAdapter(custom_zpt,
                           (Interface, IDummyBrowserLayer, IView, IDummyPortletManager, Interface),
                           provided=IPortletRenderer, name='portlet')

    @classmethod
    def tearDown(self):
        zope.component.testing.tearDown()


class TestPortletResourceType(unittest.TestCase):
    layer = PortletResourceTestLayer

    def setUp(self):
        self.rt = PortletResourceType()

    def test_resource_order_and_attributes(self):
        resources = list(self.rt)
        self.assertEqual(len(resources), 3)
        
        # first resource: local registration, specific browser layer
        res = resources[0]
        self.assertEqual(res.name, 'portlet')
        self.assertEqual(res.type, 'portlet')
        self.assertEqual(res.description, u'Portlet for * in the plone.app.themeeditor.tests.test_portlets.IDummyPortletManager manager')
        self.assertEqual(res.info, 'In the database: portal_view_customizations/customized_portlet')
        self.assertEqual(res.context, ('zope.interface.Interface', 'plone.app.themeeditor.tests.test_portlets.IDummyPortletManager'))
        self.assertEqual(res.layer, 'plone.app.themeeditor.tests.test_portlets.IDummyBrowserLayer')
        self.assertEqual(res.actions, [('Edit', 'customized_portlet/manage_main'),
                                       ('Remove', '/manage_delObjects?ids=customized_portlet')])
        self.assertEqual(set(res.tags), set(['portlet','customized']))

        # second resource: global registration, specific browser layer
        res = resources[1]
        self.assertEqual(res.name, 'portlet')
        self.assertEqual(res.type, 'portlet')
        self.assertEqual(res.description, u'Portlet for * in the plone.app.themeeditor.tests.test_portlets.IDummyPortletManager manager')
        self.failUnless(res.info.startswith(u'On the filesystem: '))
        self.failUnless(res.info.endswith(u'plone/app/themeeditor/tests/cmf_test_skins/test/test.pt'))
        self.assertEqual(res.context, ('zope.interface.Interface', 'plone.app.themeeditor.tests.test_portlets.IDummyPortletManager'))
        self.assertEqual(res.layer, 'plone.app.themeeditor.tests.test_portlets.IDummyBrowserLayer')
        self.assertEqual(res.actions, [('View', '/@@customizezpt.html?required=zope.interface.Interface,plone.app.themeeditor.tests.test_portlets.IDummyBrowserLayer,zope.browser.interfaces.IView,plone.app.themeeditor.tests.test_portlets.IDummyPortletManager,zope.interface.Interface&view_name=portlet')])
        self.assertEqual(res.tags, ['portlet'])

        # third resource: global registration, general browser layer
        res = resources[2]
        self.assertEqual(res.name, 'portlet')
        self.assertEqual(res.type, 'portlet')
        self.assertEqual(res.description, u'Portlet for * in the plone.app.themeeditor.tests.test_portlets.IDummyPortletManager manager')
        self.failUnless(res.info.startswith(u'On the filesystem: '))
        self.failUnless(res.info.endswith(u'plone/app/themeeditor/tests/cmf_test_skins/test/test.pt'))
        self.assertEqual(res.context, ('zope.interface.Interface', 'plone.app.themeeditor.tests.test_portlets.IDummyPortletManager'))
        self.assertEqual(res.layer, 'zope.publisher.interfaces.browser.IBrowserRequest')
        self.assertEqual(res.actions, [('View', '/@@customizezpt.html?required=zope.interface.Interface,zope.publisher.interfaces.browser.IBrowserRequest,zope.browser.interfaces.IView,plone.app.themeeditor.tests.test_portlets.IDummyPortletManager,zope.interface.Interface&view_name=portlet')])
        self.assertEqual(res.tags, ['portlet'])

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
