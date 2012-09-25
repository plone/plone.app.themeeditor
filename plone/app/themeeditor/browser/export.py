#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import basename
from paste.script import command
from plone.app.themeeditor.interfaces import _
from plone.app.themeeditor.interfaces import IResourceRetriever
from plone.app.themeeditor.utils import dumpSkin
from plone.z3cform.layout import FormWrapper
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from templer.localcommands import TemplerLocalCommand
from z3c.form import form, field, button
from zope import interface, schema
from zope.component import getUtility
import fileinput
import logging
import os
import shutil
import sys
import tarfile
import tempfile

JBOTCOMPATIBLE = ('zopeview', 'portlet', 'view', 'viewlet')
_templates_dir = os.path.join(os.path.dirname(__file__))
_templates_dir = os.path.join(_templates_dir, '..', 'templates')

LOGGER = 'plone.app.themeeditor'


class JBOTResourceException(Exception):

    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


def info(msg, *args):
    logging.getLogger(LOGGER).info(msg, *args)


class IThemeEditorExportForm(interface.Interface):

    name = schema.TextLine(title=_(u'Name'))
    version = schema.TextLine(title=_(u'Version'))
    description = schema.TextLine(title=_(u'Description'))
    author = schema.TextLine(title=_(u'Author'))
    author_email = schema.TextLine(title=_(u'Author Email'))


class ThemeEditorExportForm(form.Form):

    fields = field.Fields(IThemeEditorExportForm)
    ignoreContext = True  # don't use context to get widget data
    label = _(u'Export your customizations')
    template = ViewPageTemplateFile('export_form.pt')

    @button.buttonAndHandler(_(u'Export Customizations'))
    def handleApply(self, action):
        (data, errors) = self.extractData()
        if errors:
            return
        (output_dir, namespace_package, name, package_name) = \
            self.theme_skel(data)
        self.theme_populate(output_dir, namespace_package, name,
                            data['version'])
        self.write_setuppy(data, namespace_package, package_name,
                           output_dir)
        tarball = self.theme_tarball(output_dir, namespace_package,
                name, data['version'])
        self.theme_download(tarball)
        shutil.rmtree(output_dir)
        return 'hello universe'

    def theme_skel(self, data):
        ''' method that generates a theme skeleton '''
        name = data.pop('name')
        data['add_profile'] = True
        (data['namespace_package'], data['package']) = name.split('.')
        (tpl, create, output_dir) = _create_tpl()
        info('ThemeEditorExportForm.theme_skel: Creating theme skeleton outputdir=%s, theme_name=%s'
             , output_dir, name)
        vars = [str('%s=%s') % (k, v) for (k, v) in data.items()]

        create.run([
            '--no-interactive',
            '--output-dir',
            output_dir,
            '-t',
            'plone_basic',
            name,
            ] + vars)
        cwd = os.getcwd()
        try:
            os.chdir('/'.join([output_dir, name, 'src']))
            add = TemplerLocalCommand('add')
            add.template_vars['view_name'] = 'example'
            add.run(['browserview', 'view_name=example'])
        finally:
            os.chdir(cwd)
        package_name = name

        return (output_dir, data['namespace_package'], data['package'],
                package_name)

    def theme_populate(
        self,
        output_dir,
        namespace_package,
        name,
        make_jbot_zcml=0,
        dump_cmfskins=0,
        base_theme='Plone Default',
        version='100',
        ):
        '''
        retreive all the customized items and export to the theme_skel
        '''

        rm = getUtility(IResourceRetriever)
        customized_resources = list(rm.iter_resources(tags=['customized'
                                    ]))

        # iterate over customized resources and export to theme_skel

        for resource in customized_resources:
            resource = resource[0]
            if resource.type in JBOTCOMPATIBLE:
                make_jbot_zcml = 1
                self.resource_to_jbot(resource, output_dir,
                        namespace_package, name)
            else:
                dump_cmfskins = 1
                try:
                    base_theme = resource.base_skin
                except AttributeError:
                    base_theme = ''
        if dump_cmfskins == 1:
            self.dump_cmfskins(output_dir, namespace_package, name,
                               base_theme, version)
        if make_jbot_zcml == 1:
            self.create_jbot_zcml(output_dir, namespace_package, name)
        self.write_zcml_and_generic_setup(output_dir,
                namespace_package, name, base_theme, version)

    def write_setuppy(
        self,
        data,
        namespace_package,
        package_name,
        output_dir,
        ):

        setup_vars = {
            'version': data['version'],
            'theme_name': package_name,
            'namespace_package': namespace_package,
            'namespace': namespace_package,
            'theme_description': data['description'],
            'author': data['author'],
            'author_email': data['author_email'],
            }
        template = os.path.join(_templates_dir, 'setup.py.tmpl')
        output_file = os.path.join(output_dir, package_name, 'setup.py')
        self.write_tmpl(template, output_file, vars=setup_vars)

    def theme_tarball(
        self,
        output_dir,
        namespace_package,
        name,
        version='0',
        ):
        '''
        convert the theme into a tarball
        '''

        tarballname = '%s.%s-%s.tar.gz' % (namespace_package, name,
                version)

        # while working, we store the original directory so that we can
        # reset it later

        original_dir = os.getcwd()
        os.chdir(output_dir)
        tar = tarfile.open('sample.tar.gz', 'w:gz')
        tar = tarfile.open(tarballname, 'w:gz')
        tar.add('%s.%s' % (namespace_package, name))
        tar.close()

        # reset the working directory if we don't do this, it won't be
        # able to find the egg_info_dir in the future

        os.chdir(original_dir)
        return os.path.join(output_dir, tarballname)

    def theme_download(self, path, blocksize=32768):
        self.context.REQUEST.RESPONSE.setHeader('content-type',
                'application/x-tar')
        self.context.REQUEST.RESPONSE.setHeader('content-length',
                str(os.stat(path)[6]))
        self.context.REQUEST.RESPONSE.setHeader('Content-Disposition',
                ' attachment; filename=' + basename(path))
        download = open(path, 'rb')
        while True:
            data = download.read(blocksize)
            if data:
                self.context.REQUEST.RESPONSE.write(data)
            else:
                break
        download.close()

    def dump_cmfskins(
        self,
        output_dir,
        namespace_package,
        name,
        base_theme,
        version,
        ):
        '''
        convert resource to filesystem directory
        '''
        zmi_skin_names = ['custom']
        fs_dest_directory = output_dir
        fs_product_name = '%s.%s' % (namespace_package, name)
        dumpSkin(self.context, zmi_skin_names, fs_dest_directory,
                 fs_product_name, erase_from_skin=0)

    def write_zcml_and_generic_setup(
        self,
        output_dir,
        namespace_package,
        name,
        base_theme,
        version,
        ):

        package_name = '%s.%s' % (namespace_package, name)

        # overwrite the existing skins.zcml file

        skin_vars = {
            'name': name,
            'namespace': namespace_package,
            'package_name': package_name,
            'theme_name': package_name,
            'base_theme': base_theme,
            'version': version,
            }

        template = os.path.join(_templates_dir, 'skins.zcml.tmpl')
        output_file = os.path.join(
            output_dir,
            package_name,
            'src',
            namespace_package,
            name,
            'skins.zcml',
            )
        self.write_tmpl(template, output_file, vars=skin_vars)

        # custom skins.xml

        template = os.path.join(_templates_dir, 'skins.xml.tmpl')
        output_file = os.path.join(
            output_dir,
            package_name,
            'src',
            namespace_package,
            name,
            'profiles',
            'default',
            'skins.xml',
            )
        self.write_tmpl(template, output_file, vars=skin_vars)

        # custom viewlets.xml

        template = os.path.join(_templates_dir, 'viewlets.xml.tmpl')
        output_file = os.path.join(
            output_dir,
            package_name,
            'src',
            namespace_package,
            name,
            'profiles',
            'default',
            'viewlets.xml',
            )
        self.write_tmpl(template, output_file, vars=skin_vars)

        # custom metadata.xml

        template = os.path.join(_templates_dir, 'metadata.xml.tmpl')
        output_file = os.path.join(
            output_dir,
            package_name,
            'src',
            namespace_package,
            name,
            'profiles',
            'default',
            'metadata.xml',
            )
        self.write_tmpl(template, output_file, vars=skin_vars)

        # custom profile.zcml

        template = os.path.join(_templates_dir, 'profiles.zcml.tmpl')
        output_file = os.path.join(
            output_dir,
            package_name,
            'src',
            namespace_package,
            name,
            'profiles.zcml',
            )
        self.write_tmpl(template, output_file, vars=skin_vars)

        # custom browser/configure.zcml

        template = os.path.join(_templates_dir,
                                'browser_configure.zcml.tmpl')
        output_file = os.path.join(
            output_dir,
            package_name,
            'src',
            namespace_package,
            name,
            'browser',
            'configure.zcml',
            )
        self.write_tmpl(template, output_file, vars=skin_vars)

    def write_tmpl(
        self,
        tmpl,
        output_file,
        vars,
        ):

        _template = open(tmpl)
        _content = _template.read()
        _template.close()
        _content = _content % vars
        f = open(output_file, 'w')
        f.write(_content)
        f.close()

    def resource_to_jbot(
        self,
        resource,
        output_dir,
        namespace_package,
        name,
        ):
        '''
        convert resource to just a bunch of templates (jbot)
        we assume that this is an already customized resource
        '''

        try:
            resource_info = self.jbot_resource_info(resource)
        except JBOTResourceException:

            # XXX Fixme - should use a more robust test skip this
            # resource

            return
        (jbotname, tmpl_text) = resource_info
        package_name = '%s.%s' % (namespace_package, name)

        jbot_dir = os.path.join(output_dir, package_name, 'src',
                                namespace_package, name, 'jbot')

        if not os.path.exists(jbot_dir):
            os.makedirs(jbot_dir)
        jbot_file = os.path.join(jbot_dir, jbotname)
        f = open(jbot_file, 'w')
        f.write(tmpl_text)
        f.close()

    def create_jbot_zcml(
        self,
        output_dir,
        namespace_package,
        name,
        ):

        package_name = '%s.%s' % (namespace_package, name)
        jbot_vars = {'package_name': package_name}
        template = os.path.join(_templates_dir, 'jbot.zcml.tmpl')
        output_file = os.path.join(output_dir, package_name, 'src',
                                   namespace_package, name, 'jbot.zcml')
        self.write_tmpl(template, output_file, vars=jbot_vars)

        configure_zcml = os.path.join(output_dir, package_name, 'src',
                namespace_package, name, 'configure.zcml')

        # insert jbot zcml file include (after the 9th line)

        for (i, line) in enumerate(fileinput.input(configure_zcml,
                                   inplace=1)):
            sys.stdout.write(line)
            if i == 8:
                sys.stdout.write('  <include file="jbot.zcml" />\n')

    def jbot_resource_info(self, resource):
        rm = getUtility(IResourceRetriever)
        resources = rm.iter_resources(name=resource.name,
                exact=True).next()
        if resources[-1].info.startswith(u'On the filesystem'):
            path = resources[-1].path
        else:
            raise JBOTResourceException('%s is not a working properly with jbot this may be a bug in plone.app.themeeditor '
                    , resource.name)
        context_prefix = resources[-1].context[-1].split('.interfaces'
                )[0]
        jbotname = '.'.join([context_prefix, basename(path)])
        tmpl_text = resource.text
        return (jbotname, tmpl_text)


class ThemeEditorExportView(FormWrapper):

    form = ThemeEditorExportForm

    def __init__(self, context, request):
        FormWrapper.__init__(self, context, request)
        request.set('disable_border', 1)


def _create_tpl():
    commands = command.get_commands()
    create = commands['create'].load()
    create = create('any name here')
    output_dir = tempfile.mkdtemp()

    # tpl = zopeskel.plone3_theme.Plone3Theme("new template")

    tpl = None

    return (tpl, create, output_dir)
