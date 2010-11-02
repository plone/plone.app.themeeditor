from Products.CMFCore.utils import getToolByName
import itertools
from zope.component import getGlobalSiteManager, getSiteManager
from zope.app.component.hooks import getSite
from plone.app.themeeditor.interfaces import IResourceType
from plone.app.themeeditor.interfaces import IResourceRegistration
from zope.interface import implements
from plone.app.customerize.registration import templateViewRegistrationInfos
from plone.memoize.instance import memoize
from five.customerize.interfaces import ITTWViewTemplate
from zope.i18n import translate

# get the message factory
from plone.app.themeeditor.interfaces import _

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
        return list(request.__provides__.__iro__)
    
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
            res.context = context = required[0]
            if context == 'zope.interface.Interface':
                context = '*'
            res.description = translate(_('View for X',
                                default = u'View for ${context}',
                                mapping = {u'context': context}))
            res.layer = required[1]
            res.actions = []
            res.tags = ['template']
            res.path = None
            if info['customized']:
                res.tags.append('customized')
                obj = getattr(pvc, info['customized'])
                res.path = '/'.join(obj.getPhysicalPath())
                res.text = obj._text
                res.info = translate(_('In the database',
                             default = u'In the database: ${path}',
                             mapping = {'path': res.path}))
                res.actions.append(('Edit', obj.absolute_url() + '/manage_main'))
                remove_url = pvc.absolute_url() + '/manage_delObjects?ids=' + info['customized']
                res.actions.append(('Remove', remove_url))
            else:
                res.path = info['zptfile']
                res.info = translate(_(u"On the filesystem", 
                               default=u"On the filesystem: ${path}",
                               mapping={u"path" : res.path}))
                view_url = pvc.absolute_url() + '/@@customizezpt.html?required=%s&view_name=%s' % (info['required'], info['viewname'])
                res.actions.append(('View', view_url))
            name = info['viewname'].lower()
            if name.endswith('.css'):
                res.tags.append('stylesheet')
            elif name.endswith('.js'):
                res.tags.append('javascript')
            elif name.endswith('.kss'):
                res.tags.append('kss')
            elif name.endswith('.jpg') or name.endswith('.gif') or name.endswith('.png'):
                res.tags.append('image')
                
            yield res
    
    def export(self, context):
        """ return the resource information 
            context is the export context
        """
        context.writeDataFile() 
