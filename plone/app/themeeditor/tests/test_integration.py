import unittest
from niteoweb.windmill import WindmillTestCase
from Products.PloneTestCase.setup import setupPloneSite
from Products.PloneTestCase.layer import onsetup
from Products.Five.zcml import load_config
from Testing import ZopeTestCase as ztc

@onsetup
def load_zcml():
    import plone.app.themeeditor
    load_config('configure.zcml', plone.app.themeeditor)
    ztc.installPackage('plone.app.themeeditor')

load_zcml()
setupPloneSite(products=['plone.app.themeeditor'])

class ThemeEditorIntegrationTestCase(WindmillTestCase):

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
        client.click(id=u'plone-app-themeeditor-name-field')
        client.type(text=u'logo', id=u'plone-app-themeeditor-name-field')
        client.click(id=u'plone-app-themeeditor-filter-button')
        client.waits.forElement(timeout=u'', id=u'plone-app-themeeditor-browser')
        client.click(jquery=u"('dt[id^=themeeditor-logo.jpg] a')[0]")
        client.waits.forElement(xpath=u"//dd[@class='plone-app-themeeditor-layers']")
        client.click(jquery=u"('a[href*=plone_images/logo.jpg/manage_main]')[0]")
        client.waits.forElement(jquery=u"('#pb_1 input[value=Customize]')")
        client.click(name=u'submit')
        client.waits.forElement(timeout=u'', id=u'pb_2')
        # XXX for now we don't have a good way to actually make an assertion that
        # the customized image is rendered instead...at least we can make sure
        # there's now a 'Remove' link which we can use
        client.click(id=u'plone-app-themeeditor-name-field')
        client.type(text=u'logo', id=u'plone-app-themeeditor-name-field')
        client.click(id=u'plone-app-themeeditor-filter-button')
        client.waits.forElement(timeout=u'', jquery=u"('dt[id^=themeeditor-logo.jpg]')[0]")
        client.click(jquery=u"('dt[id^=themeeditor-logo.jpg] a')[0]")
        client.waits.forElement(xpath=u"//dd[@class='plone-app-themeeditor-layers']")
        client.click(link=u'Remove')

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
