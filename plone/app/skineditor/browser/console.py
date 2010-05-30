from zope.component import getUtility
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.skineditor.interfaces import IResourceRetriever
from plone.memoize.instance import memoize

class SkinsConsole(BrowserView):
    
    console = ViewPageTemplateFile('console.pt')
    layers = ViewPageTemplateFile('layers.pt')

    main_template = 'main_template'

    def index(self):
        try:
            return self.console()
        except:
            self.main_template = '@@failsafe_main_template'
            return self.console()
    
    @memoize
    def results(self, exact=False, customized=None):
        name = self.request.form.get('name')
        rm = getUtility(IResourceRetriever)
        return list(rm.iter_resources(name=name, exact=exact, customized=customized))
