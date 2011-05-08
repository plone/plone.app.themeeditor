##############################################################################
#
#  This code is borrowed from the qPloneSkinDump Product
#
##############################################################################
"""Skin dump Utility
"""
from AccessControl import ClassSecurityInfo
from Globals import DTMLFile
from Globals import package_home
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile


import os, re, string, sets, time
from zope.component import queryMultiAdapter
from App.config import getConfiguration
from Products.CMFCore.utils import getToolByName

#from config import *
from write_utils import writeProps, writeFileContent, writeObjectsMeta

from zope.interface import providedBy
from zope.schema import getFields
from zope.component import getMultiAdapter, getUtility, getSiteManager
from zope.publisher.interfaces.browser import IBrowserRequest
from five.customerize.interfaces import IViewTemplateContainer, ITTWViewTemplate
from plone.portlets.interfaces import IPortletAssignmentMapping, IPortletManager, IPlacelessPortletManager
from plone.portlets.interfaces import IPortletContext, IPortletDataProvider
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.app.customerize.registration import generateIdFromRegistration, interfaceName

from Products.GenericSetup.utils import _getDottedName, _resolveDottedName
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.context import BaseContext

CSS_PATTERN = re.compile("^.+\.css$")
JS_PATTERN = re.compile("^.+\.js$")
_write_custom_meta_type_list = [
    'Controller Page Template',
    'Controller Python Script',
    'Controller Validator',
    'DTML Method',
    'File',
    'Image',
    'Page Template',
    'Script (Python)' ]
_acceptable_meta_types = _write_custom_meta_type_list + ['Folder',]
ospJoin = os.path.join

def get_product_listdirs():
    """ Return a contents of all plugged in Products directories."""
    products = sets.Set()
    [products.update(os.listdir(product_dir)) for product_dir in Products.__path__]
    return products

def get_id(obj):
    """ Get real object's id."""
    id = callable(obj.id) and obj.id() or obj.id
    assert obj.getId() == id, "expected identical ids: '%s' != '%s'" % (obj.getId(), id)
    return id

def getData(obj, meta_type):
    """ Return object's data."""
    if meta_type in ['Image', 'File']:
         output = obj.data
    else:
        try:
            output = obj.document_src()
        except AttributeError:
            # XXX Fixme now fails silently (though it should never fail, add a test for this silent fail)
            return
    return output
    

def dumpPortalViewCustomization(context):
    result = []

    components = getSiteManager(context)
    localregs = [reg for reg in components.registeredAdapters() if (len(reg.required) in (2, 4, 5) and
                                                                     reg.required[1].isOrExtends(IBrowserRequest) and
                                                                     ITTWViewTemplate.providedBy(reg.factory))]
    container = getUtility(IViewTemplateContainer)
    for lreg in localregs:
        ttw_id = lreg.factory.__name__
                            
        if ttw_id not in container.objectIds():
            continue
        ttw = getattr(container, ttw_id)
        ttw_info = {'for_name'  : interfaceName(lreg.required[0]),
                    'type_name' : interfaceName(lreg.required[-1]),
                    'view_name' : lreg.name,
                    'kwargs'    : {'text' : ttw._text,
                                   'content_type' : ttw.content_type,
                                   'encoding' : ttw.output_encoding,
                                   }}
        result.append(ttw_info)

    return result

def extractInfoFromAssignment(name, assignment):
    klass = assignment.__class__
    a = {'name' : name, 'class' : '%s' % _getDottedName(klass)}
    data = assignment.data
    kwargs = {}
    for i in list(providedBy(data)):
        if i.isOrExtends(IPortletDataProvider):
            for field_name, field in getFields(i).items():
                kwargs[field_name] = field.get(assignment)
    a['kwargs'] = kwargs
    return a

def extractSiteWidePortlets(context, managers):
    """ Extract site-wide portlets 
        Data structure:
            '__site-wide-portlets__', [(<manager1_name>, <manager1_info>),
                                       (<manager2_name>, <manager2_info>),
                                       (<manager3_name>, <manager3_info>)])
            <manager_info>:
                {'category1' : <catmapping1>,
                 'category2' : <catmapping2>}
            <catmapping>:
                {'key1' : <mapping1>,
                 'key2' : <mapping2>}
            <mapping>:
                {'assignment_name1' : <assignment1>,
                 'assignment_name2' : <assignment2>}
            <assignment>:
                {'name'   : 'Assignment',
                 'class'  : 'dotted.path.to.assignment.class',
                 'kwargs' : {'parameter1' : 'value1',
                             'parameter2' : 'value2'}
    """
    info = []
    for manager_name, manager in managers:
        manager_info = {}
        for category, catmapping in manager.items():
            catmapping_info = {}
            for key, mapping in catmapping.items():
                mapping_info = {}
                for name, assignment in mapping.items():
                    mapping_info[name] = extractInfoFromAssignment(name, assignment)
                catmapping_info[key] = mapping_info
            manager_info[category] = catmapping_info
        info.append((manager_name, manager_info))
    return info

def extractContextPortletsFromManager(context, manager):
    """ Extract all contextual portlets from given object and portlet manager, and portlets blacklists
        Data structure:
        <manager_info> =
            {'blacklists'  : [(GROUP_CATEGORY, True),
                              (CONTENT_TYPE_CATEGORY, False),
                              (CONTEXT_CATEGORY, None)],
             'assignments' : [{'name'   : 'Assignment-2',
                               'class'  : 'dotted.path.to.assignment.class',
                               'kwargs' : {'parameter1' : 'value1',
                                          'parameter2' : 'value2'}},
                              {'name'   : 'Assignment',
                               'class'  : 'dotted.path.to.assignment.class',
                               'kwargs' : {'parameter1' : 'value1',
                                            'parameter2' : 'value2'}]}
    """

    info = {}
    info['assignments'] = assignments = []
    info['blacklists'] = blacklists = []

    # Extract contextual portlets
    mapping = getMultiAdapter((context, manager), IPortletAssignmentMapping, context=context)
    for name, assignment in mapping.items():
        assignments.append(extractInfoFromAssignment(name, assignment))

    # Extract blacklists for given object and manager
    localassignmentmanager = getMultiAdapter((context, manager), ILocalPortletAssignmentManager)
    blacklist = localassignmentmanager._getBlacklist()
    if blacklist is not None:
        for category, key in blacklist.items():
            blacklists.append((category, key))

    return info

def extractPortletsFromContext(context, slot_structure, typesToShow, managers):
    """ Extract portlets for given object assigned through all portlet managers.
        Data structure:
            ('unique/path/to/context', [(<manager1_name>, <manager1_info>),
                                        (<manager2_name>, <manager2_info>),
                                        (<manager3_name>, <manager3_info>)])
    """


    info = []
    key = '/'.join(context.getPhysicalPath()[2:])

    for name, manager in managers:
        info.append((name, extractContextPortletsFromManager(context, manager)))

    slot_structure.append((key, info))

    return slot_structure

def dumpAllPortlets(context, slot_structure, typesToShow, managers):
    extractPortletsFromContext(context, slot_structure, typesToShow, managers)
    if getattr(context.aq_base, 'isPrincipiaFolderish', 0):
        for id, obj in context.contentItems():
            if obj.portal_type in typesToShow:
                dumpAllPortlets(obj, slot_structure, typesToShow, managers)

    return slot_structure

def dumpPortlets(context, dump_policy, dump_portlets_selection):
    """ Extract portlets from given set of objects and site-wide portlets too.
        Data structure:
            SLOT_STRUCTURE =
                [(), (), ()]
    """

    portal = getToolByName(context, 'portal_url').getPortalObject()
    portal_state = getMultiAdapter((portal, context.REQUEST), name=u'plone_portal_state')
    typesToShow = portal_state.friendly_types()

    components = getSiteManager(context)
    managers = [r for r in components.registeredUtilities() if r.provided.isOrExtends(IPortletManager)]
    context_managers = [(m.name, getUtility(IPortletManager, name=m.name, context=context)) for m in managers
                                                                               if not IPlacelessPortletManager.providedBy(m.component)]
    managers = [(m.name, getUtility(IPortletManager, name=m.name, context=context)) for m in managers]

    slot_structure = []
    if dump_policy == 'root':
        extractPortletsFromContext(portal, slot_structure, typesToShow, context_managers)
    elif dump_policy == 'all':
        dumpAllPortlets(portal, slot_structure, typesToShow, context_managers)
    elif dump_policy == 'selection':
        for ppath in dump_portlets_selection:
            obj = portal.restrictedTraverse(ppath)
            extractPortletsFromContext(obj, slot_structure, typesToShow, context_managers)

    slot_structure.append(('__site-wide-portlets__', extractSiteWidePortlets(portal, managers)))

    return slot_structure

def buildSkinLayers(context, zmi_base_skin_name):
    pskins = getToolByName(context,'portal_skins')
    layers = (pskins.getSkinPath(zmi_base_skin_name) or '').split(',')
    return "\n".join(['   <layer name="%s"/>' % l for l in layers])

def getFSSkinPath(folder, fs_dest_directory, fs_product_name):
    """ Return file system skin path for subdir."""

    folder_path = '/'.join(folder.getPhysicalPath()[list(folder.getPhysicalPath()).index('portal_skins')+1:])
    namespace,name = fs_product_name.split('.')
    skins_folder = "%s_%s_%s_templates" % (namespace,name,folder_path)
    skinpath = os.path.join(fs_dest_directory,
                            fs_product_name, namespace, name,
                            'skins',skins_folder)

    return skinpath

def dumpFolder(folder, fs_dest_directory, fs_product_name):
    skinpath = getFSSkinPath(folder, fs_dest_directory, fs_product_name)
    # Create directory in FS if not yet exist
    if not os.path.exists(skinpath):
        os.makedirs(skinpath)
    # Loop of copying content from ZMIskin-folder to FSskin-folder 
    obj_meta = {}
    for o in folder.objectValues():
        meta_type = o.meta_type
        id = get_id(o)
        if meta_type in _acceptable_meta_types:
            # Adding to .objects all acceptable meta_types.
            # Fixing bug of id-meta_type confusing.
            obj_meta[id] = meta_type
        if meta_type == 'Folder':
            # very plone specific
            if id in ['stylesheet_properties', 'base_properties'] or id.startswith('base_properties'):
                writeProps(o, skinpath, extension = '.props')
            else:
                dumpFolder(o, fs_product_name, fs_product_name)
        elif meta_type in _write_custom_meta_type_list:
            #writeProps( o, skinpath )      # write object's properties
            # extract content from object(depend on metatype) and write it to the file
            writeFileContent(o, skinpath, getData(o, meta_type))
        else:
            print 'method ignoring ', meta_type
    # write '.objects' file to directory if present objects with id without extension
    if obj_meta :
        writeObjectsMeta(obj_meta, skinpath)

def dumpSkin(context, skin_names=['custom',], fs_dest_directory=None,
             fs_product_name='QSkinTemplate', erase_from_skin=0):
    """Dump custom information to file."""
    if type(skin_names) not in (type([]), type(())):
        skin_names = [skin_names,]
    for skin_name in list(skin_names):
        folder = getToolByName(context, 'portal_skins')[skin_name]
        dumpFolder(folder, fs_dest_directory, fs_product_name)
        # delete objects from the skin, if request
        if erase_from_skin:
            folder.manage_delObjects(ids = folder.objectIds())

def fillinFileTemplate(f_path_read, f_path_write=None, dict={}):
    """ Fillin file template with data from dictionary."""
    if not f_path_write:
        f_path_write = f_path_read
    f_tmpl = open(f_path_read, 'r')
    tmpl = f_tmpl.read()
    f_tmpl.close()
    f_tmpl = open(f_path_write, 'w')
    try:
       f_tmpl.write(tmpl % dict)
    except:
        raise str(tmpl)
    f_tmpl.close()

def getResourcesList(directory, resources_list, pattern=CSS_PATTERN):
    """ Get resources list from 'directory' skin folder."""
    for o in directory.objectValues():
        meta_type = o.meta_type
        id = get_id(o)
        if meta_type == 'Folder':
            # very plone specific
            if id not in ['stylesheet_properties', 'base_properties'] \
               and not id.startswith('base_properties'):
                css_list = getResourcesList(o, resources_list, pattern)
        elif pattern.match(id):
            resources_list.append( id )
    return resources_list
 
def getResourceProperties(context, regestry_id, prop_list, dflt=''):
    """ Return list of dictionaries with all dumped resources properties."""
    properties=[]
    resource = getToolByName(context, regestry_id, None)
    if resource:
        for res in resource.getResources():
            props = {}
            for prop in prop_list:
                accessor = getattr(res, 'get%s' % prop.capitalize(), None)
                if accessor:
                    props[prop] = accessor() or dflt
            properties.append(props)
    return properties

def getResourceListRegdata(context, subdir, rsrc_pattern, rsrc_name, rsrc_reg_props):
    rsrc_list = getResourcesList(subdir, resources_list=[], pattern=rsrc_pattern)#---CSS--#000000#aabbcc
    result_rsrc_list = []
    [result_rsrc_list.append(item) for item in rsrc_list if item not in result_rsrc_list]
    skin_css_regdata = getResourceProperties(context, rsrc_name, rsrc_reg_props)   # Get Data from CSS Regestry
    return result_rsrc_list, skin_css_regdata

def copyDir(srcDirectory, dstDirectory, productName):
    """Recursive copying from ZMIskin-folder to FS one""" 
    for item in os.listdir(srcDirectory):
        src_path = ospJoin(srcDirectory, item)
        dst_path = ospJoin(dstDirectory, item)
        if os.path.isfile(src_path):
            if os.path.exists(dst_path):
                continue
            f_sorce = open(src_path,'r')
            data = f_sorce.read()
            f_sorce.close()
            f_dst = open(dst_path,'w')
            f_dst.write(data)
            f_dst.close()
        elif os.path.isdir(src_path) \
             and not ".svn" in src_path:
            if not os.path.exists(dst_path):
                os.mkdir(dst_path)
            copyDir(src_path, dst_path, productName)

def fsDirectoryViewsXML(folder_names, product_name, remove=False):
    pattern = """ <object name="%(folder_name)s" meta_type="Filesystem Directory View"
       directory="Products.%(product_name)s:skins/%(folder_name)s" %(remove)s/>\n"""
    xml = ''
    if type(folder_names) not in (type([]), type(())):
        folder_names = [folder_names,]
    for name in folder_names:
       xml += pattern % {'product_name' : product_name, \
                         'folder_name'  : name, \
                         'remove'       : remove and 'remove="True"' or '', \
                        }
    return xml

def makeNewProduct(context, destinationDir, productName, productSkinName, \
                   zmi_skin_names, zmi_base_skin_name, subdir,\
                   doesCustomizeSlots, left_slots, right_slots, slot_forming, main_column, \
                   doesExportObjects, import_policy, dump_CSS, dump_JS, \
                   dump_portlets, dump_policy, dump_portlets_selection, dump_custom_views):
    """Create new skin-product's directory and 
       copy skin-product template with little modification"""
    products_path = destinationDir
    productPath = ospJoin(products_path, productName)
    if not (productName in os.listdir(products_path)):
        os.mkdir(productPath)
    files_to_remove = []
    files_to_add    = []
    # Form CSS and JS importing list and regestry data (looking in subdir too) for Plone 2.1.0+ 
    stylesheets_xml = ''
    javascripts_xml = ''
    #subdir = subdir or getToolByName(context, 'portal_skins')[zmi_skin_name]
    portal_setup = getToolByName(context, 'portal_setup')
    result_css_list = skin_css_regdata = result_js_list = skin_js_regdata = []
    base_context = BaseContext(portal_setup, portal_setup.getEncoding())
    if dump_CSS:
        res_reg = getToolByName(context, 'portal_css', None)
        exporter = queryMultiAdapter((res_reg, base_context), IBody)
        if exporter is not None:
            stylesheets_xml = exporter.body
        #result_css_list, skin_css_regdata = getResourceListRegdata(context, subdir,
                                            #CSS_PATTERN, 'portal_css', CSS_REG_PROPS)
    if stylesheets_xml == '':
        files_to_remove.append(ospJoin('profiles', 'default', 'cssregistry.xml'))
    if dump_JS:
        res_reg = getToolByName(context, 'portal_javascripts', None)
        exporter = queryMultiAdapter((res_reg, base_context), IBody)
        if exporter is not None:
            javascripts_xml = exporter.body
        #result_js_list, skin_js_regdata = getResourceListRegdata(context, subdir,
                                            #JS_PATTERN, 'portal_javascripts', JS_REG_PROPS)
    if javascripts_xml == '':
        files_to_remove.append(ospJoin('profiles', 'default', 'jsregistry.xml'))

    slots = ()
    if dump_portlets:
        slots = dumpPortlets(context, dump_policy, dump_portlets_selection)

    # Get Slots customization information
    if not doesCustomizeSlots:
        left_slots = right_slots = None
        slot_forming = main_column = None

    # Prepare XML strings for add to skins.xml
    skin_layers = buildSkinLayers(context, zmi_base_skin_name)

    # Prepare profiles
    default_marker, afterinstall_marker, uninstall_marker = {}, {}, {}
    profiles = ['default', 'afterinstall', 'uninstall']
    profiles_path = ospJoin(products_path, productName, 'profiles')
    for profile in profiles:
        varname = "%s_marker" % profile
        file_name = "%s_%s.txt" % (productName.lower(), profile)
        locals()[varname].update({'fname' : file_name, \
                                  'fpath' : ospJoin(profiles_path, profile, file_name), \
                                  'fdata' : "# Marker file for %s profile of %s skin" % \
                                            (profile, productName) })
        files_to_add.append(locals()[varname])

    # dump customized objects from portal_view_customization
    custom_views = []
    if dump_custom_views:
        custom_views = dumpPortalViewCustomization(context)

    # Copy skin_template to SKIN_PRODUCT directory
    templatePath = ospJoin(PRODUCTS_PATH, PROJECTNAME, TEMPLATE_PATH)
    copyDir(templatePath, productPath, productName)
    # Form data dictionary and form Skin Product's files
    conf_dict = {"IMPORT_POLICY" : import_policy \
                ,"GENERATOR_PRODUCT" : PROJECTNAME \
                ,"SKIN_PRODUCT_NAME" : productName \
                ,"SKIN_NAME" : productSkinName \
                ,"BASE_SKIN_NAME" : zmi_base_skin_name \
                ,"DUMP_CSS": not not dump_CSS \
                ,"DUMP_JS": not not dump_JS \
                ,"CSS_LIST" : str(result_css_list) \
                ,"JS_LIST" : str(result_js_list) \
                ,"SKIN_CSS_REGDATA" : str(skin_css_regdata) \
                ,"SKIN_JS_REGDATA" : str(skin_js_regdata) \
                ,"LEFT_SLOTS" : str(left_slots) \
                ,"RIGHT_SLOTS" : str(right_slots) \
                ,"SLOT_FORMING" : slot_forming \
                ,"MAIN_COLUMN" : main_column \
                ,"product_name" : productName \
                ,"skin_name" : productSkinName \
                ,"skin_name_lowercase" : productSkinName.lower() \
                ,"skin_name_capital" : '%s%s' % (productSkinName[0].upper(), productSkinName[1:]) \
                ,"product_name_lowercase" : productName.lower() \
                ,"viewlets_zcml" : '' \
                ,"stylesheets_xml" : stylesheets_xml \
                ,"javascripts_xml" : javascripts_xml \
                ,"version" : time.strftime('%Y%m%d') \
                ,"slot_structure" : str(slots) \
                ,"skin_layers" : skin_layers \
                ,"custom_views" : str(custom_views) \
                ,"directory_views_xml" : fsDirectoryViewsXML(zmi_skin_names, productName) \
                ,"remove_directory_views_xml" : fsDirectoryViewsXML(zmi_skin_names, productName, remove=True) \
                ,"creation_date" : time.strftime('%d/%m/%Y') \
                ,"install_profile_marker" : default_marker['fname'] \
                ,"afterinstall_profile_marker" : afterinstall_marker['fname'] \
                ,"uninstall_profile_marker" : uninstall_marker['fname'] \
    }
    sp_updated_files = ['config.py' \
                       ,'README.txt' \
                       ,'HISTORY.txt' \
                       ,'setuphandlers.py' \
                       ,'uninstallhandlers.py' \
                       ,'profiles.zcml' \
                       ,'utils.py' \
                       ,'configure.zcml' \
                       ,'skins.zcml' \
                       ,ospJoin('Extensions', 'Install.py')\
                       ,ospJoin('browser', 'interfaces.py')\
                       ,ospJoin('browser', 'viewlets.zcml')\
                       ,ospJoin('browser', 'configure.zcml')\
                       ,ospJoin('profiles', 'default', 'skins.xml')\
                       ,ospJoin('profiles', 'default', 'cssregistry.xml')\
                       ,ospJoin('profiles', 'default', 'jsregistry.xml')\
                       ,ospJoin('profiles', 'default', 'propertiestool.xml')\
                       ,ospJoin('profiles', 'afterinstall', 'import_steps.xml')\
                       ,ospJoin('profiles', 'uninstall', 'import_steps.xml')\
                       ,ospJoin('profiles', 'uninstall', 'skins.xml')\
                       ,ospJoin('browser', 'configure.zcml') \
                       #,ospJoin('profiles', 'uninstall', 'cssregistry.xml')\
                       #,ospJoin('profiles', 'uninstall', 'jsregistry.xml')\
                       ]
    for fp in sp_updated_files:
        fillinFileTemplate(ospJoin(productPath, fp), dict=conf_dict)
    for fp in files_to_remove:
        os.remove(ospJoin(productPath,fp))
    for data in files_to_add:
        f = file(data['fpath'],'w')
        f.write(data['fdata'])
        f.close()
