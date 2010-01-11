from Products.CMFCore.utils import getToolByName
from Products.CMFCore.FSObject import FSObject
from persistent import Persistent
from zope.app.component.hooks import getSite
from plone.app.skineditor.interfaces import IResourceType
from plone.app.skineditor.interfaces import IResourceRegistration
from zope.interface import implements, Interface

class CMFResourceRegistration(object):
    implements(IResourceRegistration)
        
class CMFSkinsResourceType(object):
    """
    Test setup.
      >>> from plone.app.skineditor.cmf import CMFSkinsResourceType
    
    Make sure we can iterate the resources:
      >>> resources = list(o for o in CMFSkinsResourceType())
      >>> len(resources) > 0
      True
    
    Make sure the first resource found looks reasonable:
      >>> resources[0].__dict__
      {'layer': 'Images', 'description': u'CMF skin item', 'title': 'preview_icon.png', 'registrations': [<plone.app.skineditor.cmf.CMFResourceRegistration object at ...>], 'context': <InterfaceClass zope.interface.Interface>, 'type': 'cmf_skins', 'name': 'preview_icon.png'}
    """
    
    implements(IResourceType)
    name = 'cmfskins'

    skins_tool = None
    skin = None
    
    def __init__(self, skin=None):
        self.skin = skin
    
    def __iter__(self):
        """ Returns an iterator enumerating the resources of this type. """
        if self.skins_tool is None:
            self.skins_tool = getToolByName(getSite(), 'portal_skins')
        if self.skin is None:
            self.skin = self.skins_tool.getDefaultSkin()
        
        for layer_path in self.skins_tool.getSkinPath(self.skin).split(','):
            layer_folder = self.skins_tool.unrestrictedTraverse(layer_path)
            for name, obj in layer_folder.items():
                res = CMFResourceRegistration()
                res.name = name
                res.type = self.name
                res.context = Interface
                res.description = u'CMF skin item'
                res.layer = layer_path
                res.actions = []
                if isinstance(obj, FSObject):
                    res.info = 'On the filesystem: %s' % obj._filepath
                    res.actions.append(('View', obj.absolute_url() + '/manage_main'))
                elif isinstance(obj, Persistent):
                    res.info = 'In the database: %s' % '/'.join(obj.getPhysicalPath())
                    res.actions.append(('Edit', obj.absolute_url() + '/manage_main'))
                    res.actions.append(('Remove', obj.aq_parent.absolute_url() + '/manage_delObjects?ids=' + obj.getId()))
                yield res
    
    def __getitem__(self, name):
        raise NotImplemented
    
    def export(self, context):
        raise NotImplemented
