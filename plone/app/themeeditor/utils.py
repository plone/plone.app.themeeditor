#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Skin dump Utility
"""

import os
import re

# from config import *

from plone.app.themeeditor.write_utils import writeProps, \
    writeFileContent, writeObjectsMeta
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

