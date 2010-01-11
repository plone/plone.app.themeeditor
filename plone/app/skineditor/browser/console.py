from zope.component import getUtility
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.skineditor.interfaces import IResourceRetriever
from plone.memoize.instance import memoize

class SkinsConsole(BrowserView):
    
    index = ViewPageTemplateFile('console.pt')
    layers = ViewPageTemplateFile('layers.pt')
    
    @memoize
    def results(self, exact=False):
        name = self.request.form.get('name')
        rm = getUtility(IResourceRetriever)
        return list(rm.iter_resources(name=name, exact=exact))
