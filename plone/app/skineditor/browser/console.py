from zope.component import getUtility
from Products.Five import BrowserView
from plone.app.skineditor.interfaces import IResourceRetriever
from plone.memoize.instance import memoize

class SkinsConsole(BrowserView):
    
    @memoize
    def results(self):
        name = self.request.form.get('name')
        rm = getUtility(IResourceRetriever)
        return list(rm.iter_resources(name=name))
