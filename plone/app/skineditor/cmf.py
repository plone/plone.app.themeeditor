from Products.CMFCore.utils import getToolByName
from Products.CMFCore.FSObject import FSObject
from persistent import Persistent
from zope.app.component.hooks import getSite
from plone.app.skineditor.interfaces import IResourceType
from plone.app.skineditor.interfaces import IResource, IResourceRegistration
from zope.interface import implements, Interface

class CMFResource(object):
    implements(IResource)

class CMFResourceRegistration(object):
    implements(IResourceRegistration)
        
class CMFSkinsResourceType(object):
    """
    Test setup.
      >>> from plone.skins.cmf import CMFSkinsResourceType
    
    Make sure we can iterate the resources:
      >>> resources = list(o for o in CMFSkinsResourceType())
      >>> len(resources) > 0
      True
    
    Make sure the first resource found looks reasonable:
      >>> resources[0].__dict__
      {'layer': 'Images', 'description': u'CMF skin item', 'title': 'preview_icon.png', 'registrations': [<plone.app.skineditor.cmf.CMFResourceRegistration object at ...>], 'context': <InterfaceClass zope.interface.Interface>, 'type': 'cmf_skins', 'name': 'preview_icon.png'}
      >>> resources[0].registrations[0].__dict__
      {'info': 'On the filesystem: /.../Products/CMFDefault/skins/Images/preview_icon.png', 'active': True, 'actions': [('View', 'http://nohost/cmf/portal_skins/Images/preview_icon.png/manage_main')], 'title': 'Images'}
    """
    
    implements(IResourceType)
    
    name = 'cmfskins'
    precedence = 1
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
        
        regs = {}
        for layer_path in self.skins_tool.getSkinPath(self.skin).split(','):
            layer_folder = self.skins_tool.unrestrictedTraverse(layer_path)
            # build map of name to items, ordered by layer precedence
            for name, obj in layer_folder.items():
                regs.setdefault(name, []).append((layer_path, obj))
                # TODO recurse
        for name, layer_map in regs.iteritems():
            res = CMFResource()
            res.name = name                
            res.type = self.name
            res.context = Interface
            res.title = name
            res.description = u'CMF skin item'
            res.registrations = []
            for i, (layer_name, obj) in enumerate(layer_map):
                reg = CMFResourceRegistration()
                reg.title = res.layer = layer_name
                reg.actions = []
                if isinstance(obj, FSObject):
                    reg.info = 'On the filesystem: %s' % obj._filepath
                    reg.actions.append(('View', obj.absolute_url() + '/manage_main'))
                elif isinstance(obj, Persistent):
                    reg.info = 'In the database: %s' % '/'.join(obj.getPhysicalPath())
                    reg.actions.append(('Edit', obj.absolute_url() + '/manage_main'))
                    reg.actions.append(('Remove', obj.aq_parent.absolute_url() + '/manage_delObjects?ids=' + obj.getId()))
                reg.active = (i == 0)
                res.registrations.append(reg)
            yield res
    
    def __getitem__(self, name):
        raise NotImplemented
    
    def export(self, context):
        raise NotImplemented
