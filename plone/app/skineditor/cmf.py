from Products.CMFCore.utils import getToolByName
from Products.CMFCore.FSObject import FSObject
from Products.CMFCore.DirectoryView import DirectoryViewSurrogate
from persistent import Persistent
from zope.app.component.hooks import getSite
from plone.app.skineditor.interfaces import IResourceType
from plone.app.skineditor.interfaces import IResourceRegistration
from zope.interface import implements, Interface
from zope.pagetemplate.interfaces import IPageTemplate
from OFS.Image import Image
from Products.CMFCore.FSImage import FSImage
from Products.CMFCore.FSPythonScript import FSPythonScript, CustomizedPythonScript
from Products.CMFFormController.FSControllerValidator import FSControllerValidator
from Products.CMFFormController.FSControllerPythonScript import FSControllerPythonScript
from Products.CMFCore.FSDTMLMethod import FSDTMLMethod

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
            layer_folder = self.skins_tool.unrestrictedTraverse(layer_path)
            for name, obj in layer_folder.items():
                res = CMFResourceRegistration()
                res.name = name
                res.layer = layer_path
                res.actions = []
                res.icon = obj.icon
                res.tags = []
                if isinstance(obj, FSObject):
                    res.info = 'On the filesystem: %s' % obj._filepath
                    res.path = obj._filepath
                    res.actions.append(('View', obj.absolute_url() + '/manage_main'))
                elif isinstance(obj, Persistent) and not isinstance(obj, DirectoryViewSurrogate):
                    res.tags.append('customized')
                    res.path = '/'.join(obj.getPhysicalPath())
                    res.info = 'In the database: ' + res.path
                    res.actions.append(('Edit', obj.absolute_url() + '/manage_main'))
                    res.actions.append(('Remove', obj.aq_parent.absolute_url() + '/manage_delObjects?ids=' + obj.getId()))
                elif isinstance(obj, Persistent):
                    res.path = '/'.join(obj.getPhysicalPath())
                    res.info = 'In the database: ' + res.path
                    
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
