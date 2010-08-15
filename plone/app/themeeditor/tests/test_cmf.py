import unittest

from Products.CMFCore.SkinsTool import SkinsTool
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CMFCore.DirectoryView import addDirectoryViews

from OFS.Folder import Folder
from OFS.Image import Image

from plone.app.themeeditor.cmf import CMFSkinsResourceType

class CMFResourceTestLayer:
    
    @classmethod
    def setUp(self):
        tool = self.skins_tool = SkinsTool()
        registerDirectory('cmf_test_skins', globals())
        addDirectoryViews(tool, 'cmf_test_skins', globals())
        tool.addSkinSelection('test', 'test')

class TestCMFResourceType(unittest.TestCase):
    layer = CMFResourceTestLayer

    def setUp(self):
        self.layer.skins_tool.manage_properties(default_skin='test')
        self.rt = CMFSkinsResourceType(skins_tool = self.layer.skins_tool)

    def test_iter(self):
        resources = list(self.rt)
        self.failUnless(resources)
        res = resources[0]
        
        self.assertEqual(res.base_skin,'test')
        self.assertEqual(res.name, 'test')
        self.assertEqual(res.type, 'cmfskins')
        self.assertEqual(res.context, 'zope.interface.Interface')
        self.assertEqual(res.description, u'CMF skin item')
        self.assertEqual(res.layer, 'test')
        self.assertEqual(res.info, 'On the filesystem')
        self.failUnless(res.info.mapping['path'].endswith('cmf_test_skins/test/test.pt'))
        self.failUnless(res.path.endswith('cmf_test_skins/test/test.pt'))
        self.assertEqual(res.actions, [('View', 'test/test/manage_main')])
        self.assertEqual(res.tags, ['template'])

    def test_only_items_in_current_skin_path_found(self):
        self.layer.skins_tool.manage_properties(default_skin='nonexistent')
        self.failIf(list(self.rt))
    
    def test_customized_resource(self):
        tool = self.layer.skins_tool
        tool['folder'] = Folder('folder')
        tool.folder['image'] = Image('image', 'image', 'data')
        tool.addSkinSelection('folder', 'folder', make_default=1)
        res = list(self.rt)[0]
        
        self.assertEqual(res.info, 'In the database')
        self.assertEqual(res.info.mapping, {'path': 'portal_skins/folder/image'})
        self.assertEqual(res.path, 'portal_skins/folder/image')
        self.assertEqual(res.actions, [('Edit', 'folder/image/manage_main'),
                                       ('Remove', 'folder/manage_delObjects?ids=image')])
        self.assertEqual(set(res.tags), set(['image','customized']))
    
    def test_items_returned_in_skin_layer_order(self):
        tool = self.layer.skins_tool
        tool['test2'] = Folder('test2')
        tool.test2['image2'] = Image('image2', 'image2', 'data')
        tool.test2['image3'] = Image('image3', 'image3', 'data')
        
        tool.addSkinSelection('multi', 'test,test2', make_default=1)
        resource_ids = [res.name for res in self.rt]
        self.assertEqual(resource_ids, ['test', 'image2', 'image3'])
        
        tool.addSkinSelection('multi', 'test2,test')
        resource_ids = [res.name for res in self.rt]
        self.assertEqual(resource_ids, ['image2', 'image3', 'test'])

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
