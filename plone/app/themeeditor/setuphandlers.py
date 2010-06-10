from Products.CMFCore.utils import getToolByName

def uninstall(context):
    
    if not context.readDataFile('plone.app.themeeditor-uninstall.txt'):
        return
    
    cp = getToolByName(context.getSite(), 'portal_controlpanel')
    cp.unregisterApplication("plone.app.themeeditor")