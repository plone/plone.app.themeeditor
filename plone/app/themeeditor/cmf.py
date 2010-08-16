from Products.CMFCore.utils import getToolByName
from Products.CMFCore.FSObject import FSObject
from Products.CMFCore.DirectoryView import DirectoryViewSurrogate
from persistent import Persistent
from zope.app.component.hooks import getSite
from plone.app.themeeditor.interfaces import IResourceType
from plone.app.themeeditor.interfaces import IResourceRegistration
from zope.interface import implements, Interface
from zope.pagetemplate.interfaces import IPageTemplate
from OFS.Image import Image
from Products.CMFCore.FSImage import FSImage
from Products.CMFCore.FSPythonScript import FSPythonScript, CustomizedPythonScript
from Products.CMFFormController.FSControllerValidator import FSControllerValidator
from Products.CMFFormController.FSControllerPythonScript import FSControllerPythonScript
from Products.CMFCore.FSDTMLMethod import FSDTMLMethod
# translation machinery
from plone.app.themeeditor.interfaces import  _
# borrow from plone message factory
from zope.i18nmessageid import MessageFactory
PMF = MessageFactory('plone')

class CMFResourceRegistration(object):
    implements(IResourceRegistration)
    
    type = 'cmfskins'
    context = Interface.__identifier__
    description = u'CMF skin item'

class CMFSkinsResourceType(object):
    implements(IResourceType)
    name = 'cmfskins'

    skins_tool = None
    skin = None
    
    def __init__(self, skins_tool=None, skin=None):
        self.skins_tool = skins_tool
        self.skin = skin
    
    def __iter__(self):
        if self.skins_tool is None:
            self.skins_tool = getToolByName(getSite(), 'portal_skins')
        if self.skin is None:
            self.skin = self.skins_tool.getDefaultSkin()
        
        skin_path = self.skins_tool.getSkinPath(self.skin)
        if skin_path is None:
            return
        for layer_path in skin_path.split(','):
            try:
                layer_folder = self.skins_tool.unrestrictedTraverse(layer_path)
            except KeyError:
                # Sometimes the active theme declares nonexistent folders
                # this is not themeeditors fault, so we skip the error
                continue
            for name, obj in layer_folder.items():
                res = CMFResourceRegistration()
                res.base_skin = self.skin
                res.name = name
                res.layer = layer_path
                res.actions = []
                res.icon = obj.icon
                res.tags = []
                res.path = None
                if isinstance(obj, FSObject):
                    res.info = _('On the filesystem',
                                 default=u'On the filesystem: ${path}',
                                 mapping = {'path': obj._filepath})
                    res.path = obj._filepath
                    res.actions.append((PMF(u'View'), obj.absolute_url() + '/manage_main'))
                elif isinstance(obj, Persistent) and not isinstance(obj, DirectoryViewSurrogate):
                    res.tags.append('customized')
                    res.path = '/'.join(obj.getPhysicalPath())
                    #res.info = 'In the database: ' + res.path
                    res.info = _(u"In the database", 
                               default=u"In the database: ${path}",
                               mapping={u"path" : res.path})
                    res.actions.append((PMF(u'Edit'), obj.absolute_url() + '/manage_main'))
                    res.actions.append((PMF(u'Remove'), obj.aq_parent.absolute_url() + '/manage_delObjects?ids=' + obj.getId()))
                elif isinstance(obj, Persistent):
                    res.path = '/'.join(obj.getPhysicalPath())
                    res.info = 'In the database: ' + res.path
                    res.info = _(u"In the database", 
                               default=u"In the database: ${path}",
                               mapping={u"path" : res.path})
                    
                if IPageTemplate.providedBy(obj):
                    res.tags.append('template')
                    
                if isinstance(obj, Image) or isinstance(obj, FSImage):
                    res.tags.append('image')
                elif isinstance(obj, FSPythonScript) or isinstance(obj, CustomizedPythonScript):
                    res.tags.append('python-script')
                elif isinstance(obj, FSControllerValidator) or \
                 isinstance(obj, FSControllerPythonScript):
                    res.tags.append('controller-page-template')
                elif isinstance(obj, FSDTMLMethod):
                    res.tags.append('dtml')
                    
                id = obj.getId().lower()
                if id.endswith('.css'):
                    res.tags.append('stylesheet')
                elif id.endswith('.js'):
                    res.tags.append('javascript')
                elif id.endswith('.kss'):
                    res.tags.append('kss')
                    
                yield res
    
    def export(self, context):
        raise NotImplemented
