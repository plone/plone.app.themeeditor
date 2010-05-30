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
    type = 'zopeview'
    icon = '/misc_/PageTemplates/zpt.gif'

class ZopeViewResourceType(object):
    implements(IResourceType)
    name = 'zopeview'

    @memoize
    def layer_precedence(self):
        request = getSite().REQUEST
        return request.__provides__.__iro__
    
    def iter_view_registrations(self):
        gsm = getGlobalSiteManager()
        sm = getSiteManager()
        layer_precedence = self.layer_precedence()
        for reg in itertools.chain(gsm.registeredAdapters(), sm.registeredAdapters()):
            if len(reg.required) != 2:
                continue
            if reg.required[1] not in layer_precedence:
                continue
            if getattr(reg.factory, '__name__', '').startswith('SimpleViewClass') \
                    or ITTWViewTemplate.providedBy(reg.factory):
                yield reg

    def __iter__(self):
        """ Returns an iterator enumerating the resources of this type. """
        pvc = getToolByName(getSite(), 'portal_view_customizations')
        layer_precedence = self.layer_precedence()
        by_layer_precedence_and_ttwness = lambda x: (layer_precedence.index(x.required[1]), int(not ITTWViewTemplate.providedBy(x.factory)))
        regs = sorted(self.iter_view_registrations(), key=by_layer_precedence_and_ttwness)
        for info in templateViewRegistrationInfos(regs, mangle=False):
            required = info['required'].split(',')
            res = ViewResourceRegistration()
            res.name = info['viewname']
            res.context = required[0]
            if res.context == 'zope.interface.Interface':
                res.description = 'View for *'
            else:
                res.description = u'View for %s' % required[0]
            res.layer = required[1]
            res.actions = []
            res.tags = ['template']
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
            if info['viewname'].endswith('.css'):
                res.tags.append('stylesheet')
            if info['viewname'].endswith('.js'):
                res.tags.append('javascript')
            yield res
    
    def export(self, context):
        raise NotImplemented
