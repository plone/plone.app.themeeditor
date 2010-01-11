from Products.CMFCore.utils import getToolByName
import itertools
from zope.component import getGlobalSiteManager, getSiteManager
from zope.app.component.hooks import getSite
from plone.app.skineditor.interfaces import IResourceType
from plone.app.skineditor.interfaces import IResourceRegistration
from zope.interface import implements
from plone.app.customerize.registration import templateViewRegistrationInfos
from plone.memoize.instance import memoize
from five.customerize.interfaces import ITTWViewTemplate

class ViewResourceRegistration(object):
    implements(IResourceRegistration)

class ZopeViewResourceType(object):
    """
    Test setup.
      >>> from plone.app.skineditor.zopeview import ZopeViewResourceType
    
    Make sure we can iterate the resources:
      >>> resources = list(o for o in ZopeViewResourceType())
      >>> len(resources) > 0
      True
    
    Make sure the first resource found looks reasonable:
      >>> resources[0].__dict__
      {'layer': 'Images', 'description': u'CMF skin item', 'title': 'preview_icon.png', 'registrations': [<plone.app.skineditor.cmf.CMFResourceRegistration object at ...>], 'context': <InterfaceClass zope.interface.Interface>, 'type': 'cmf_skins', 'name': 'preview_icon.png'}
    """
    
    implements(IResourceType)
    name = 'zopeview'

    @memoize
    def layer_precedence(self):
        request = getSite().REQUEST
        return request.__provides__.__iro__
    
    def iter_view_registrations(self):
        gsm = getGlobalSiteManager()
        sm = getSiteManager()
        for reg in itertools.chain(gsm.registeredAdapters(), sm.registeredAdapters()):
            if len(reg.required) != 2:
                continue
            if reg.required[1] not in self.layer_precedence():
                continue
            if getattr(reg.factory, '__name__', '').startswith('SimpleViewClass') \
                    or ITTWViewTemplate.providedBy(reg.factory):
                yield reg
    
    def __iter__(self):
        """ Returns an iterator enumerating the resources of this type. """
        pvc_path = '/'.join(getToolByName(getSite(), 'portal_view_customizations').getPhysicalPath())
        layer_precedence = self.layer_precedence()
        by_layer_precedence_and_ttwness = lambda x: (layer_precedence.index(x.required[1]), int(not ITTWViewTemplate.providedBy(x.factory)))
        regs = sorted(self.iter_view_registrations(), key=by_layer_precedence_and_ttwness)
        for info in templateViewRegistrationInfos(regs, mangle=False):
            required = info['required'].split(',')
            res = ViewResourceRegistration()
            res.name = info['viewname']
            res.type = self.name
            res.context = required[0]
            if res.context == 'zope.interface.Interface':
                res.description = 'View for *'
            else:
                res.description = u'View for %s' % required[0]
            res.layer = required[1]
            res.actions = []
            if info['customized']:
                path = pvc_path + '/' + info['customized']
                res.info = 'In the database: %s' % path
            else:
                res.info = 'On the filesystem: %s' % info['zptfile']
            yield res
    
    def export(self, context):
        raise NotImplemented
