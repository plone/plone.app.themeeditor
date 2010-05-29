from Products.CMFCore.utils import getToolByName
from Products.CMFCore.FSObject import FSObject
from persistent import Persistent
from zope.app.component.hooks import getSite
from plone.app.skineditor.interfaces import IResourceType
from plone.app.skineditor.interfaces import IResourceRegistration
from zope.interface import implements, Interface

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
                if isinstance(obj, FSObject):
                    res.info = 'On the filesystem: %s' % obj._filepath
                    res.actions.append(('View', obj.absolute_url() + '/manage_main'))
                elif isinstance(obj, Persistent):
                    res.info = 'In the database: %s' % '/'.join(obj.getPhysicalPath())
                    res.actions.append(('Edit', obj.absolute_url() + '/manage_main'))
                    res.actions.append(('Remove', obj.aq_parent.absolute_url() + '/manage_delObjects?ids=' + obj.getId()))
                yield res
    
    def export(self, context):
        raise NotImplemented
