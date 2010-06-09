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
        ztc.utils.setupCoreSessions(self.app)
        self.setRoles(['Manager'])
        self.login_user()

    def test_customize_logo(self):
        client = self.wm
        client.click(id=u'user-name')
        # load customizer
        client.click(link=u'Site Setup')
        client.waits.forPageLoad(timeout=u'20000')
        client.click(link=u'Theme Editor')
        # go into advanced mode and customize based on the logo in the
        # non-active "plone_images" layer (Windmill doesn't do file uploads)
        client.click(link=u'Advanced')
        client.click(id=u'plone-app-skineditor-name-field')
        client.type(text=u'logo', id=u'plone-app-skineditor-name-field')
        client.click(id=u'plone-app-skineditor-filter-button')
        client.waits.forElement(timeout=u'', id=u'plone-app-skineditor-browser')
        client.click(xpath=u"//a[@id='skineditor-logo.png']/dt")
        client.waits.forElement(xpath=u"//dd[@class='plone-app-skineditor-layers']")
        client.click(jquery=u"('a[href*=plone_images/logo.png/manage_main]')[0]")
        client.waits.forElement(jquery=u"('#pb_1 input[value=Customize]')")
        client.click(name=u'submit')
        client.waits.forElement(timeout=u'', id=u'pb_2')
        # now reload and make sure the logo has the height we expect from the
        # customized image
        client.refresh()
        client.asserts.assertJS(js=u"$('#portal-logo').height() == 57")
        # now remove the customization
        client.click(id=u'plone-app-skineditor-name-field')
        client.type(text=u'logo', id=u'plone-app-skineditor-name-field')
        client.click(id=u'plone-app-skineditor-filter-button')
        client.waits.forElement(timeout=u'', id=u'skineditor-logo.png')
        client.click(xpath=u"//a[@id='skineditor-logo.png']/dt")
        client.waits.forElement(xpath=u"//dd[@class='plone-app-skineditor-layers']")
        client.click(link=u'Remove')
        # and confirm we're back to the original height
        client.refresh()
        client.asserts.assertJS(js=u"$('#portal-logo').height() == 56")

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
