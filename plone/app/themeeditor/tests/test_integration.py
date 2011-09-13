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
        client.click(name=u'x-browser')
        client.waits.forElement(timeout=u'', id=u'pb_3')
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

    def test_exporter(self):
        client = self.wm
        client.click(id=u'user-name')
        # load customizer
        client.click(link=u'Site Setup')
        client.waits.forPageLoad(timeout=u'20000')
        client.click(link=u'Theme Editor')
        client.click(link=u'Export')
        # client.waits.forPageLoad(timeout=u'20000')
        client.waits.forElement(timeout=u'', id=u'form-widgets-name')
        # fill out the form
        client.type(text=u'plonetheme.test', id=u'form-widgets-name')
        client.type(text=u'1.0', id=u'form-widgets-version')
        client.type(text=u'A Theme to test this', id=u'form-widgets-description')
        client.type(text=u'John Doe', id=u'form-widgets-author')
        client.type(text=u'john.doe@example.com', id=u'form-widgets-author_email')
        # export the theme
        # XXX not sure why it doesn't actually generate the download
        client.click(id=u'form-buttons-4578706f727420437573746f6d697a6174696f6e73')
        # client.waits.forPageLoad(timeout=u'200')
        client.click(xpath=u"//div[@id='pb_2']/div[1]")

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
