import itertools
from zope.component import getUtilitiesFor
from zope.interface import implements
from plone.app.skineditor.interfaces import IResourceRetriever
from plone.app.skineditor.interfaces import IResourceType

class ResourceRetriever(object):
    """
    A resource retriever implements the IResourceRetriever interface.
      >>> from zope.interface import Interface
      >>> from zope.interface.verify import verifyClass
      >>> from zope.component import getSiteManager
      >>> verifyClass(IResourceRetriever, ResourceRetriever)
      True
    
    To demonstrate its use, we need to define a resource type that knows how
    to find a dummy resource, and register it as a named IResourceType utility:
      >>> class DummyResource(object):
      ...     type = 'dummy'
      ...     def __init__(self, **kw):
      ...         self.__dict__.update(kw)
      >>> class DummyResourceType(object):
      ...     name = 'dummy'
      ...     precedence = 1
      ...     def __iter__(self):
      ...         yield DummyResource(
      ...             name = 'dummy1',
      ...             description = 'test resource',
      ...             context = Interface,
      ...             )
      >>> sm = getSiteManager()
      >>> sm.registerUtility(DummyResourceType(), provided=IResourceType, name=u'dummy')
      
    Now we can create a ResourceRetriever and use it to query the available
    resource types:
      >>> rm = ResourceRetriever()
      >>> list(rm.iter_resource_types())
      [<plone.app.skineditor.retriever.DummyResourceType object at ...>]
      
    And we can query the resource manager for available resources:
      >>> list(rm.iter_resources())
      [[<plone.app.skineditor.retriever.DummyResource object at ...>]]
      >>> len(list(rm.iter_resources(name='dummy')))
      1
      >>> len(list(rm.iter_resources(name='Dummy')))
      1
      >>> len(list(rm.iter_resources(name='foobar')))
      0
      >>> len(list(rm.iter_resources(type='dummy')))
      1
      >>> len(list(rm.iter_resources(name='foobar')))
      0
      >>> len(list(rm.iter_resources(context=Interface)))
      1
      >>> len(list(rm.iter_resources(context='foobar')))
      0
    
    Clean up.
      >>> sm.unregisterUtility(provided=IResourceType, name=u'dummy')
      True
    """

    implements(IResourceRetriever)

    def iter_resource_types(self):
        for _, rt in getUtilitiesFor(IResourceType):
            yield rt
    
    def iter_resources(self, name=None, type=None, context=None, exact=False):
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
            if context is not None and context is not regs[0].context:
                continue

            yield regs
