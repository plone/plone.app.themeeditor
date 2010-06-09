import unittest
from niteoweb.windmill import WindmillTestCase
from Products.PloneTestCase.setup import setupPloneSite
from Products.PloneTestCase.layer import onsetup
from Products.Five.zcml import load_config
from Testing import ZopeTestCase as ztc

@onsetup
def load_zcml():
    import plone.app.skineditor
    load_config('configure.zcml', plone.app.skineditor)
    ztc.installPackage('plone.app.skineditor')

load_zcml()
setupPloneSite(products=['plone.app.skineditor'])

class SkinEditorIntegrationTestCase(WindmillTestCase):

    def afterSetUp(self):
        """Setup for each test
        """
        self.setRoles(['Manager'])
        self.login_user()

    def test_dummy(self):
        import pdb; pdb.set_trace( )

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
