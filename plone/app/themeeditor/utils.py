#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Skin dump Utility
"""

import os
import re
import sets
import time

from five.customerize.interfaces import IViewTemplateContainer, \
    ITTWViewTemplate
from Products.GenericSetup.context import BaseContext
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.utils import _getDottedName
from zope.component import getMultiAdapter, getUtility, getSiteManager
from zope.component import queryMultiAdapter
from zope.interface import providedBy
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.schema import getFields

# from config import *

from plone.app.customerize.registration import interfaceName
from plone.app.themeeditor.write_utils import writeProps, \
    writeFileContent, writeObjectsMeta
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.interfaces import IPortletAssignmentMapping, \
    IPortletManager, IPlacelessPortletManager
from plone.portlets.interfaces import IPortletDataProvider
from Products.CMFCore.utils import getToolByName

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
    'Script (Python)',
    ]
_acceptable_meta_types = _write_custom_meta_type_list + ['Folder']
ospJoin = os.path.join


def get_product_listdirs():
    """ Return a contents of all plugged in Products directories."""

    products = sets.Set()
    [products.update(os.listdir(product_dir)) for product_dir in
     Products.__path__]
    return products


def get_id(obj):
    """ Get real object's id."""

    id = callable(obj.id) and obj.id() or obj.id
    assert obj.getId() == id, "expected identical ids: '%s' != '%s'" \
        % (obj.getId(), id)
    return id


def getData(obj, meta_type):
    """ Return object's data."""

    if meta_type in ['Image', 'File']:
        output = obj.data
    else:
        try:
            output = obj.document_src()
        except AttributeError:

            # XXX Fixme now fails silently (though it should never fail,
            # add a test for this silent fail)

            return
    return output


def dumpPortalViewCustomization(context):
    result = []

    components = getSiteManager(context)
    localregs = [reg for reg in components.registeredAdapters()
                 if len(reg.required) in (2, 4, 5)
                 and reg.required[1].isOrExtends(IBrowserRequest)
                 and ITTWViewTemplate.providedBy(reg.factory)]
    container = getUtility(IViewTemplateContainer)
    for lreg in localregs:
        ttw_id = lreg.factory.__name__

        if ttw_id not in container.objectIds():
            continue
        ttw = getattr(container, ttw_id)
        ttw_info = {
            'for_name': interfaceName(lreg.required[0]),
            'type_name': interfaceName(lreg.required[-1]),
            'view_name': lreg.name,
            'kwargs': {'text': ttw._text,
                       'content_type': ttw.content_type,
                       'encoding': ttw.output_encoding},
            }
        result.append(ttw_info)

    return result


def extractInfoFromAssignment(name, assignment):
    klass = assignment.__class__
    a = {'name': name, 'class': '%s' % _getDottedName(klass)}
    data = assignment.data
    kwargs = {}
    for i in list(providedBy(data)):
        if i.isOrExtends(IPortletDataProvider):
            for (field_name, field) in getFields(i).items():
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
    for (manager_name, manager) in managers:
        manager_info = {}
        for (category, catmapping) in manager.items():
            catmapping_info = {}
            for (key, mapping) in catmapping.items():
                mapping_info = {}
                for (name, assignment) in mapping.items():
                    mapping_info[name] = \
                        extractInfoFromAssignment(name, assignment)
                catmapping_info[key] = mapping_info
            manager_info[category] = catmapping_info
        info.append((manager_name, manager_info))
    return info


def extractContextPortletsFromManager(context, manager):
    """ Extract all contextual portlets from given object and portlet manager,
        and portlets blacklists
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

    mapping = getMultiAdapter((context, manager),
                              IPortletAssignmentMapping,
                              context=context)
    for (name, assignment) in mapping.items():
        assignments.append(extractInfoFromAssignment(name, assignment))

    # Extract blacklists for given object and manager

    localassignmentmanager = getMultiAdapter((context, manager),
            ILocalPortletAssignmentManager)
    blacklist = localassignmentmanager._getBlacklist()
    if blacklist is not None:
        for (category, key) in blacklist.items():
            blacklists.append((category, key))

    return info


def extractPortletsFromContext(
    context,
    slot_structure,
    typesToShow,
    managers,
    ):
    """ Extract portlets for given object assigned through
        all portlet managers
        Data structure:
            ('unique/path/to/context', [(<manager1_name>, <manager1_info>),
                                        (<manager2_name>, <manager2_info>),
                                        (<manager3_name>, <manager3_info>)])
    """

    info = []
    key = '/'.join(context.getPhysicalPath()[2:])

    for (name, manager) in managers:
        info.append((name, extractContextPortletsFromManager(context,
                    manager)))

    slot_structure.append((key, info))

    return slot_structure


def dumpAllPortlets(
    context,
    slot_structure,
    typesToShow,
    managers,
    ):

    extractPortletsFromContext(context, slot_structure, typesToShow,
                               managers)
    if getattr(context.aq_base, 'isPrincipiaFolderish', 0):
        for (id, obj) in context.contentItems():
            if obj.portal_type in typesToShow:
                dumpAllPortlets(obj, slot_structure, typesToShow,
                                managers)

    return slot_structure


def dumpPortlets(context, dump_policy, dump_portlets_selection):
    """ Extract portlets from given set of objects and site-wide portlets too.
        Data structure:
            SLOT_STRUCTURE =
                [(), (), ()]
    """

    portal = getToolByName(context, 'portal_url').getPortalObject()
    portal_state = getMultiAdapter((portal, context.REQUEST),
                                   name=u'plone_portal_state')
    typesToShow = portal_state.friendly_types()

    components = getSiteManager(context)
    managers = [r for r in components.registeredUtilities()
                if r.provided.isOrExtends(IPortletManager)]
    context_managers = [(m.name, getUtility(IPortletManager,
                        name=m.name, context=context)) for m in
                        managers
                        if not IPlacelessPortletManager.providedBy(m.component)]
    managers = [(m.name, getUtility(IPortletManager, name=m.name,
                context=context)) for m in managers]

    slot_structure = []
    if dump_policy == 'root':
        extractPortletsFromContext(portal, slot_structure, typesToShow,
                                   context_managers)
    elif dump_policy == 'all':
        dumpAllPortlets(portal, slot_structure, typesToShow,
                        context_managers)
    elif dump_policy == 'selection':
        for ppath in dump_portlets_selection:
            obj = portal.restrictedTraverse(ppath)
            extractPortletsFromContext(obj, slot_structure,
                    typesToShow, context_managers)

    slot_structure.append(('__site-wide-portlets__',
                          extractSiteWidePortlets(portal, managers)))

    return slot_structure


def buildSkinLayers(context, zmi_base_skin_name):
    pskins = getToolByName(context, 'portal_skins')
    layers = (pskins.getSkinPath(zmi_base_skin_name) or '').split(',')
    return '\n'.join(['   <layer name="%s"/>' % l for l in layers])


def getFSSkinPath(folder, fs_dest_directory, fs_product_name):
    """ Return file system skin path for subdir."""

    portal_skins_index = \
        list(folder.getPhysicalPath()).index('portal_skins')
    folder_path = '/'.join(folder.getPhysicalPath()[portal_skins_index
                           + 1:])
    (namespace, name) = fs_product_name.split('.')
    skins_folder = '%s_%s_%s_templates' % (namespace, name, folder_path)
    skinpath = ospJoin(
        fs_dest_directory,
        fs_product_name,
        'src',
        namespace,
        name,
        'skins',
        skins_folder,
        )

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

            # Adding to .objects all acceptable meta_types. Fixing bug
            # of id-meta_type confusing.

            obj_meta[id] = meta_type
        if meta_type == 'Folder':

            # very plone specific

            if id in ['stylesheet_properties', 'base_properties'] \
                or id.startswith('base_properties'):
                writeProps(o, skinpath, extension='.props')
            else:
                dumpFolder(o, fs_product_name, fs_product_name)
        elif meta_type in _write_custom_meta_type_list:

            # writeProps( o, skinpath )      # write object's properties
            # extract content from object(depend on metatype) and write
            # it to the file

            writeFileContent(o, skinpath, getData(o, meta_type))
        else:
            print 'method ignoring ', meta_type

    # write '.objects' file to directory if present objects with id
    # without extension

    if obj_meta:
        writeObjectsMeta(obj_meta, skinpath)


def dumpSkin(
    context,
    skin_names=['custom'],
    fs_dest_directory=None,
    fs_product_name='QSkinTemplate',
    erase_from_skin=0,
    ):
    """Dump custom information to file."""

    if type(skin_names) not in (type([]), type(())):
        skin_names = [skin_names]
    for skin_name in list(skin_names):
        folder = getToolByName(context, 'portal_skins')[skin_name]
        dumpFolder(folder, fs_dest_directory, fs_product_name)

        # delete objects from the skin, if request

        if erase_from_skin:
            folder.manage_delObjects(ids=folder.objectIds())


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
            resources_list.append(id)
    return resources_list


def getResourceProperties(
    context,
    regestry_id,
    prop_list,
    dflt='',
    ):
    """ Return list of dictionaries with all dumped resources properties."""

    properties = []
    resource = getToolByName(context, regestry_id, None)
    if resource:
        for res in resource.getResources():
            props = {}
            for prop in prop_list:
                accessor = getattr(res, 'get%s' % prop.capitalize(),
                                   None)
                if accessor:
                    props[prop] = accessor() or dflt
            properties.append(props)
    return properties


def getResourceListRegdata(
    context,
    subdir,
    rsrc_pattern,
    rsrc_name,
    rsrc_reg_props,
    ):

    rsrc_list = getResourcesList(subdir, resources_list=[],
                                 pattern=rsrc_pattern)  # ---CSS--#000000#aabbcc
    result_rsrc_list = []
    [result_rsrc_list.append(item) for item in rsrc_list if item
     not in result_rsrc_list]
    skin_css_regdata = getResourceProperties(context, rsrc_name,
            rsrc_reg_props)  # Get Data from CSS Regestry
    return (result_rsrc_list, skin_css_regdata)


def fsDirectoryViewsXML(folder_names, product_name, remove=False):
    pattern = \
        """ <object name="%(folder_name)s" meta_type="Filesystem Directory View"
       directory="Products.%(product_name)s:skins/%(folder_name)s" %(remove)s/>
        """
    xml = ''
    if type(folder_names) not in (type([]), type(())):
        folder_names = [folder_names]
    for name in folder_names:
        remove = ('remove="True"' if remove else '')
        xml += pattern % {'product_name': product_name,
                          'folder_name': name, 'remove': remove}
    return xml
