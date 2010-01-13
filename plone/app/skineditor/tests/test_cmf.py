import unittest

from Products.CMFCore.SkinsTool import SkinsTool
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CMFCore.DirectoryView import addDirectoryViews

from plone.app.skineditor.cmf import CMFSkinsResourceType

class CMFResourceTestLayer:
    
    @classmethod
    def setUp(self):
        tool = self.skins_tool = SkinsTool()
        registerDirectory('cmf_test_skins', globals())
        addDirectoryViews(tool, 'cmf_test_skins', globals())
        tool.addSkinSelection('test', 'test')
        tool.manage_properties(default_skin='test')

class TestResourceRetriever(unittest.TestCase):
    layer = CMFResourceTestLayer

    def setUp(self):
        self.rt = CMFSkinsResourceType(skins_tool = self.layer.skins_tool)

    def test_iter(self):
        self.failUnless(list(self.rt))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
