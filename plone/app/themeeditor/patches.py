from five.customerize.interfaces import ITTWViewTemplate
from five.customerize.browser import mangleAbsoluteFilename
from plone.app.customerize.registration import interfaceName
from five.customerize.utils import findViewletTemplate
from os.path import basename

def patch_templateViewRegistrationInfos(regs, mangle=True):
    for reg in regs:
        if ITTWViewTemplate.providedBy(reg.factory):
            zptfile = None
            zcmlfile = None
            name = reg.name or reg.factory.name
            customized = reg.factory.getId()    # TODO: can we get an absolute url?
        else:
            attr, pt = findViewletTemplate(reg.factory)
            if attr is None:        # skip, if the factory has no template...
                continue
            zptfile = pt.filename
            zcmlfile = getattr(reg.info, 'file', None)
            
            if mangle:
                zptfile = mangleAbsoluteFilename(zptfile)
                zcmlfile = zcmlfile and mangleAbsoluteFilename(zcmlfile)
            
            name = reg.name or basename(zptfile)
            customized = None
        required = [interfaceName(r) for r in reg.required]
        yield {
            'viewname': name,
            'required': ','.join(required),
            'for': required[0],
            'type': required[1],
            'zptfile': zptfile,
            'zcmlfile': zcmlfile or 'n.a.',
            'customized': customized,
        }
