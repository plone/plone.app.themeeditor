import itertools
from zope.component import getUtilitiesFor
from zope.interface import implements
from plone.app.themeeditor.interfaces import IResourceRetriever
from plone.app.themeeditor.interfaces import IResourceType

class ResourceRetriever(object):
    implements(IResourceRetriever)

    def iter_resource_types(self):
        for _, rt in getUtilitiesFor(IResourceType):
            yield rt
    
    def iter_resources(self, name=None, type=None, context=None, path=None,
            tags=None, exact=False):
        resource_types = self.iter_resource_types()
        by_name_and_context = lambda x:(x.name.lower(),x.context)
        # XXX use something Swartzian transform-like to avoid duplicate key calculation
        regs = sorted(itertools.chain(*resource_types), key=by_name_and_context)
        for _, regs in itertools.groupby(regs, key=by_name_and_context):
            regs = list(regs)
            if name is not None:
                if exact:
                    if name != regs[0].name:
                        continue
                elif name.lower() not in regs[0].name.lower():
                    continue
            if type is not None and type.lower() not in regs[0].type.lower():
                continue
            if context is not None and context.lower() not in regs[0].context.lower():
                continue
            if path is not None and path != regs[0].path:
                continue
            if tags is not None:
                if isinstance(tags, basestring):
                    tags = [tags]
                tags_found = list(tags)
                for tag in tags:
                    if tag not in regs[0].tags:
                        tags_found.remove(tag)
                if not tags_found:
                    continue

            yield regs
