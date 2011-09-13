import unittest
import zope.component.testing
from zope.component import provideAdapter
from zope.app.component.hooks import setSite, setHooks
from zope.interface import Interface
from zope.publisher.interfaces import IView
from zope.publisher.interfaces.browser import IBrowserRequest

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from five.customerize.zpt import TTWViewTemplate
from plone.app.themeeditor.viewlet import ViewletResourceType
from zope.viewlet.interfaces import IViewlet, IViewletManager
from zope.viewlet.viewlet import ViewletBase

from plone.app.themeeditor.tests.utils import IDummyBrowserLayer, DummySite

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
        self.assertEqual(res.description, 'Viewlet for * in the plone.app.themeeditor.tests.test_viewlets.IDummyViewletManager manager')
        self.assertEqual(res.info, u'In the database: /portal_view_customizations/customized_viewlet')
        self.assertEqual(res.path, '/portal_view_customizations/customized_viewlet')
        self.assertEqual(res.context, ('zope.interface.Interface', 'plone.app.themeeditor.tests.test_viewlets.IDummyViewletManager'))
        self.assertEqual(res.layer, 'plone.app.themeeditor.tests.utils.IDummyBrowserLayer')
        self.assertEqual(res.actions, [('Edit', 'portal_view_customizations/customized_viewlet/manage_main'),
                                       ('Remove', 'portal_view_customizations/manage_delObjects?ids=customized_viewlet')])
        self.assertEqual(set(res.tags), set(['viewlet','customized']))

        # second resource: global registration, specific browser layer
        res = resources[1]
        self.assertEqual(res.name, 'viewlet')
        self.assertEqual(res.type, 'viewlet')
        self.assertEqual(res.description, 'Viewlet for * in the plone.app.themeeditor.tests.test_viewlets.IDummyViewletManager manager')
        self.failUnless(res.info.startswith('On the filesystem: '))
        self.failUnless(res.info.endswith('plone/app/themeeditor/tests/cmf_test_skins/test/test.pt'))
        self.failUnless(res.path.endswith('cmf_test_skins/test/test.pt'))
        self.assertEqual(res.context, ('zope.interface.Interface', 'plone.app.themeeditor.tests.test_viewlets.IDummyViewletManager'))
        self.assertEqual(res.layer, 'plone.app.themeeditor.tests.utils.IDummyBrowserLayer')
        self.assertEqual(res.actions, [('View', 'portal_view_customizations/@@customizezpt.html?required=zope.interface.Interface,plone.app.themeeditor.tests.utils.IDummyBrowserLayer,zope.browser.interfaces.IView,plone.app.themeeditor.tests.test_viewlets.IDummyViewletManager&view_name=viewlet')])
        self.assertEqual(res.tags, ['viewlet'])

        # third resource: global registration, general browser layer
        res = resources[2]
        self.assertEqual(res.name, 'viewlet')
        self.assertEqual(res.type, 'viewlet')
        self.assertEqual(res.description, 'Viewlet for * in the plone.app.themeeditor.tests.test_viewlets.IDummyViewletManager manager')
        self.failUnless(res.info.startswith(u'On the filesystem: '))
        self.failUnless(res.info.endswith(u'plone/app/themeeditor/tests/cmf_test_skins/test/test.pt'))
        self.failUnless(res.path.endswith('cmf_test_skins/test/test.pt'))
        self.assertEqual(res.context, ('zope.interface.Interface', 'plone.app.themeeditor.tests.test_viewlets.IDummyViewletManager'))
        self.assertEqual(res.layer, 'zope.publisher.interfaces.browser.IBrowserRequest')
        self.assertEqual(res.actions, [('View', 'portal_view_customizations/@@customizezpt.html?required=zope.interface.Interface,zope.publisher.interfaces.browser.IBrowserRequest,zope.browser.interfaces.IView,plone.app.themeeditor.tests.test_viewlets.IDummyViewletManager&view_name=viewlet')])
        self.assertEqual(res.tags, ['viewlet'])

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
