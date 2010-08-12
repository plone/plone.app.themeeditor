import os
import sys
import fileinput
import tarfile
from os.path import basename
from zope import interface, schema
from z3c.form import form, field, button
from plone.z3cform.layout import wrap_form
from plone.app.themeeditor.interfaces import _
from plone.app.themeeditor.interfaces import IResourceRetriever
from five.customerize.interfaces import IViewTemplateContainer
from zope.component import getUtility
#from plone.app.themeeditor.export import TarballThemeExporter
import zopeskel
from paste.script.command import get_commands
import tempfile
import logging
JBOTCOMPATIBLE = ('portlet','view','viewlet')


LOGGER="plone.app.themeeditor"

def info(msg):
    logging.getLogger(LOGGER).info(msg)

class IThemeEditorExportForm(interface.Interface):
    name = schema.TextLine(title=_(u"Name"))
    version = schema.TextLine(title=_(u"Version"))
    description = schema.TextLine(title=_(u"Description"))
    author = schema.TextLine(title=_(u"Author"))
    author_email = schema.TextLine(title=_(u"Author Email"))

class ThemeEditorExportForm(form.Form):
    fields = field.Fields(IThemeEditorExportForm)
    ignoreContext = True # don't use context to get widget data
    label = _(u"Export your customizations")

    @button.buttonAndHandler(_(u'Export Customizations'))
    def handleApply(self, action):
        data, errors = self.extractData()
        output_dir,namespace_package,name = self.theme_skel(data)
        self.theme_populate(output_dir,namespace_package,name)
        tarball = self.theme_tarball(output_dir,namespace_package,name,data['version'])
        self.theme_download(tarball)

    def theme_skel(self,data):
        name = data.pop('name')
        data['namespace_package'],data['package'] = name.split('.')
        tpl,create,output_dir=_create_tpl()
        info("ThemeEditorExportForm.theme_skel: Creating theme skeleton outputdir=%s, theme_name=%s" % (output_dir, name) )
        vars = [str('%s=%s') % (k, v) for k,v in data.items()]
        #vars = ' '.join(vars)
        print '*' * 20, vars
        output = create.run([
                '--no-interactive',
                '--output-dir',
                output_dir,
                '-t',
                'plone3_theme',
                name,] + vars)
        return (output_dir,data['namespace_package'],data['package'])
        # not sure why an unnecessary 'example' folder gets created
        # so we remove it after the theme is created

    def theme_populate(self,output_dir,namespace_package,name,make_jbot_zcml=0):
        """
        retreive all the customized items and export to the theme_skel
        """
        # get all customized resources
        container = getUtility(IViewTemplateContainer)
        rm = getUtility(IResourceRetriever)
        customized_resources = list(rm.iter_resources(tags=['customized',]))
        # iterate over customized resources and export to theme_skel
        for resource in customized_resources:
            resource = resource[0]
            if resource.type in JBOTCOMPATIBLE:
                make_jbot_zcml = 1
                self.resource_to_jbot(resource,output_dir,namespace_package,name)
        if make_jbot_zcml == 1:
           self.create_jbot_zcml(output_dir,namespace_package,name)

    def theme_tarball(self,output_dir,namespace_package,name,version='0'):
        """
        convert the theme into a tarball
        """
        tarballname = "%s.%s-%s.tar.gz" % (namespace_package,name,version)
        os.chdir(output_dir)
        tar = tarfile.open("sample.tar.gz", "w:gz")
        tar = tarfile.open(tarballname,"w:gz")
        tar.add('%s.%s' % (namespace_package,name))
        tar.close()
        return  os.path.join(output_dir,tarballname)

    def theme_download(self,path,blocksize=32768):
        self.context.REQUEST.RESPONSE.setHeader(
                                    'content-type',
                                    'application/x-tar')
        self.context.REQUEST.RESPONSE.setHeader(
                                    'content-length',
                                    str(os.stat(path)[6]))
        self.context.REQUEST.RESPONSE.setHeader(
                                    'Content-Disposition',
                                    ' attachment; filename='+basename(path))
        download = open(path,'rb')
        while True:
            data = download.read(blocksize)
            if data:
                self.context.REQUEST.RESPONSE.write(data)
            else:
                break
        download.close()

    def resource_to_jbot(self,resource,output_dir,namespace_package,name):
        """
        convert resource to just a bunch of templates (jbot)
        we assume that this is an already customized resource
        """
        jbotname,tmpl_text = self.jbot_resource_info(resource)
        package_name = "%s.%s" % (namespace_package,name)

        jbot_dir = os.path.join(output_dir,package_name,namespace_package,name,"jbot")

        if not os.path.exists(jbot_dir):
            os.makedirs (jbot_dir)
        jbot_file = os.path.join(jbot_dir,jbotname)
        f = open(jbot_file,'w')
        f.write(tmpl_text)
        f.close()


    def create_jbot_zcml(self,output_dir,namespace_package,name):
        package_name = "%s.%s" % (namespace_package,name)
        jbot_zcml_file_content = """<configure
                             xmlns="http://namespaces.zope.org/zope"
                             xmlns:browser="http://namespaces.zope.org/browser"
                             i18n_domain="%s">

                              <include package="z3c.jbot" file="meta.zcml" />

                              <browser:jbot
                              directory="jbot"
                              layer=".browser.interfaces.IThemeSpecific" />
                         """ % package_name
        configure_zcml = os.path.join(output_dir,package_name,namespace_package,name,'configure.zcml')
        jbot_zcml_file = os.path.join(output_dir,package_name,namespace_package,name,'jbot.zcml')

        # create the jbot.zcml file
        f = open(jbot_zcml_file,'w')
        f.write(jbot_zcml_file_content)
        f.close()

        # insert jbot zcml file include after the 9th line
        for i, line in enumerate(fileinput.input(configure_zcml, inplace=1)):
            sys.stdout.write(line)
            if i == 8: sys.stdout.write('  <include file="jbot.zcml" />\n')


    def jbot_resource_info(self,resource):
        rm = getUtility(IResourceRetriever)
        resources = rm.iter_resources(name=resource.name,
                                              exact=True).next()
        if resources[-1].info == u'On the filesystem':
            path = resources[-1].path
        else:
            # XXX change this to an exception
            return "this is not a customized resource"
        context_prefix = resources[-1].context[-1].split('.interfaces')[0]
        jbotname = '.'.join([context_prefix,basename(path)])
        tmpl_text = resource.text
        return (jbotname,tmpl_text)


ThemeEditorExportView = wrap_form(ThemeEditorExportForm)

def _create_tpl():
    commands = get_commands()
    create = commands['create'].load()
    create=create('any name here')
    output_dir = tempfile.mkdtemp()
    tpl = zopeskel.plone3_theme.Plone3Theme("new template")
    return tpl,create,output_dir


