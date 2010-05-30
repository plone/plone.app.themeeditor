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
from zope.viewlet.interfaces import IViewlet

class ViewletResourceRegistration(object):
    implements(IResourceRegistration)
    type = 'viewlet'
    icon = '/misc_/PageTemplates/zpt.gif'

class ViewletResourceType(object):
    implements(IResourceType)
    name = 'viewlet'

    @memoize
    def layer_precedence(self):
        request = getSite().REQUEST
        return request.__provides__.__iro__
    
    def iter_viewlet_registrations(self):
        gsm = getGlobalSiteManager()
        sm = getSiteManager()
        layer_precedence = self.layer_precedence()
        for reg in itertools.chain(gsm.registeredAdapters(), sm.registeredAdapters()):
            if len(reg.required) != 4:
                continue
            if reg.required[1] not in layer_precedence:
                continue
            if IViewlet.implementedBy(reg.factory) or ITTWViewTemplate.providedBy(reg.factory):
                yield reg

    def __iter__(self):
        """ Returns an iterator enumerating the resources of this type. """
        pvc = getToolByName(getSite(), 'portal_view_customizations')
        layer_precedence = self.layer_precedence()
        by_layer_precedence_and_ttwness = lambda x: (layer_precedence.index(x.required[1]), int(not ITTWViewTemplate.providedBy(x.factory)))
        regs = sorted(self.iter_viewlet_registrations(), key=by_layer_precedence_and_ttwness)
        for info in templateViewRegistrationInfos(regs, mangle=False):
            required = info['required'].split(',')
            res = ViewletResourceRegistration()
            res.name = info['viewname']
            res.context = required[0], required[3]
            if required[0] == 'zope.interface.Interface':
                res.description = 'Viewlet for *'
            else:
                res.description = u'Viewlet for %s' % required[0]
            res.description += ' in the %s manager' % required[3]
            res.layer = required[1]
            res.actions = []
            res.tags = ['viewlet']
            if info['customized']:
                res.tags.append('customized')
                obj = getattr(pvc, info['customized'])
                res.path = '/'.join(obj.getPhysicalPath())
                res.info = 'In the database: %s' % res.path
                res.actions.append(('Edit', obj.absolute_url() + '/manage_main'))
                remove_url = pvc.absolute_url() + '/manage_delObjects?ids=' + info['customized']
                res.actions.append(('Remove', remove_url))
            else:
                res.info = 'On the filesystem: %s' % info['zptfile']
                res.path = info['zptfile']
                view_url = pvc.absolute_url() + '/@@customizezpt.html?required=%s&view_name=%s' % (info['required'], info['viewname'])
                res.actions.append(('View', view_url))
            yield res
    
    def export(self, context):
        raise NotImplemented
