import unittest
import zope.component.testing

from zope.component import provideUtility
from zope.interface.verify import verifyClass

from plone.app.themeeditor.interfaces import IResourceRetriever, IResourceType
from plone.app.themeeditor.retriever import ResourceRetriever

class DummyResource(object):
    type = 'dummy'
    def __init__(self, **kw):
        self.__dict__.update(kw)

class DummyResourceType(object):
    name = 'dummy'
    def __iter__(self):
        yield DummyResource(name='ZZZ_last_resource', context='Interface', path='/', tags=('template',))
        yield DummyResource(name='dummy1', context='Interface', layer='high_layer', path='/', tags=('template',))
        yield DummyResource(name='dummy1', context='Interface', layer='low_layer', path='/', tags=('template',))
        yield DummyResource(name='dummy1', context='MoreSpecificInterface', layer='low_layer', path='/', tags=('template',))

class YummyResourceType(object):
    name = 'yummy'
    def __iter__(self):
        yield DummyResource(name='dummy1', context='Interface', layer='from_yummy', path='/', tags=('template',))

class RetrieverTestLayer:
    
    @classmethod
    def setUp(self):
        provideUtility(DummyResourceType(), provides=IResourceType, name=u'dummy')
        provideUtility(YummyResourceType(), provides=IResourceType, name=u'yummy')
    
    @classmethod
    def tearDown(self):
        zope.component.testing.tearDown()

class TestResourceRetriever(unittest.TestCase):
    layer = RetrieverTestLayer

    def setUp(self):
        self.rm = ResourceRetriever()

    def filter(self, **kw):
        return list(self.rm.iter_resources(**kw))

    def testImplementsIRetriever(self):
        self.failUnless(verifyClass(IResourceRetriever, ResourceRetriever))

    def testIterResourceTypes(self):
        types = list(self.rm.iter_resource_types())
        self.failUnless(types)
        self.failUnless(isinstance(types[0], DummyResourceType))

    def testIterResources(self):
        resource_groups = list(self.filter())
        self.failUnless(resource_groups)
        resources = resource_groups[0]
        self.failUnless(resources)
        self.failUnless(isinstance(resources[0], DummyResource))
    
    def testFilterByName(self):
        self.failUnless(self.filter(name='dummy'))
        self.failUnless(self.filter(name='Dummy'))
        self.failIf(self.filter(name='foobar'))
    
    def testFilterByExactName(self):
        self.failUnless(self.filter(name='dummy1', exact=True))
        self.failIf(self.filter(name='Dummy1', exact=True))
    
    def testFilterByType(self):
        self.failUnless(self.filter(type='dummy'))
        self.failIf(self.filter(type='foobar'))
    
    def testFilterByContext(self):
        self.failUnless(self.filter(context='Interface'))
        self.failIf(self.filter(context='foobar'))
    
    def testFilterByPath(self):
        self.failUnless(self.filter(path='/'))
        self.failIf(self.filter(path='/foo'))
    
    def testFilterByTags(self):
        self.failUnless(self.filter(tags=('template',)))
        self.failIf(self.filter(tags=('foobar',)))
        self.failUnless(self.filter(tags='template'))
        self.failIf(self.filter(tags='foobar'))
    
    def testResourcesGroupedByNameAndContext(self):
        for resource_group in self.filter():
            name, context = (resource_group[0].name, resource_group[0].context)
            for resource in resource_group[1:]:
                self.failIf((resource.name, resource.context) != (name, context))
    
    def testResourceGroupsOrderedByName(self):
        self.failUnless(self.filter()[-1][0].name == 'ZZZ_last_resource')
    
    def testResourceGroupInnerOrderPreserved(self):
        self.failUnless(self.filter(name='dummy1')[0][0].layer == 'high_layer')
        self.failUnless(self.filter(name='dummy1')[0][1].layer == 'low_layer')
    
    def testResourcesFromDifferentResourceTypesInterleaved(self):
        self.failUnless(self.filter(name='dummy1')[0][2].layer == 'from_yummy')
    
def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
