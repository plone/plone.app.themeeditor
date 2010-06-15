from zope.component import getUtility
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.themeeditor.interfaces import IResourceRetriever
from plone.memoize.instance import memoize

class EditorConsole(BrowserView):
    
    console = ViewPageTemplateFile('console.pt')

    main_template = 'main_template'
    basic_tags = (
        ('customized', 'Customized Items'),
        ('template', 'Templates'),
        ('portlet', 'Portlets'),
        ('viewlet', 'Viewlets'),
        ('image', 'Images'),
        ('stylesheet', 'Stylesheets'),
        ('javascript', 'Javascripts'),
    )
    
    advanced_tags = basic_tags + (
        ('python-script', 'Python Scripts'),
        ('controller-page-template', 'CPT'),
        ('kss', 'KSS'),
        ('dtml', 'DTML')
    )
    
    @property
    @memoize
    def mode(self):
        if self.request.form.get('mode', None):
            self.request.SESSION['mode'] = self.request.form.get('mode')
        
        return self.request.SESSION.get('mode', 'basic')

    @property
    @memoize
    def available_tags(self):
        if self.mode == 'basic':
            return self.basic_tags
        else:
            return self.advanced_tags
    
    def failsafe_console(self):
        try:
            return self.console()
        except:
            self.main_template = '@@failsafe_main_template'
            return self.console()
    
    @memoize
    def results(self):
        name = self.request.form.get('name')
        default_tags = None
        if self.mode == 'basic':
            default_tags = [t[0] for t in self.available_tags]
        tag = self.request.form.get('tag', default_tags)
        rm = getUtility(IResourceRetriever)
        return list(rm.iter_resources(name=name, tags=tag))

class LayerListView(BrowserView):
    
    def lookup(self):
        name = self.request.form.get('name')
        rm = getUtility(IResourceRetriever)
        resources = rm.iter_resources(name=name, exact=True).next()
        if self.request.SESSION.get('mode', 'basic') == 'basic':
            return resources[:1]
        return resources
