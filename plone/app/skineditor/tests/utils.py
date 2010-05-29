from Acquisition import ImplicitAcquisitionWrapper
from zope.component.registry import Components
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.interface import implements
from plone.app.customerize.tool import ViewTemplateContainer

class IDummyBrowserLayer(IBrowserRequest):
    pass

class DummyRequest(object):
    implements(IDummyBrowserLayer)

class DummySite(object):
    REQUEST = DummyRequest()
    def __init__(self):
        self.registry = Components('components')
        self.portal_view_customizations = ImplicitAcquisitionWrapper(ViewTemplateContainer(), self)
    def getSiteManager(self):
        return self.registry
    def getPhysicalPath(self):
        return ('',)
