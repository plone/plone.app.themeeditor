from zope import interface, schema
from z3c.form import form, field, button
from plone.z3cform.layout import wrap_form
from plone.app.themeeditor.interfaces import _
import zopeskel
from paste.script.command import get_commands
import tempfile


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
        tpl,create,output_dir = _create_tpl()
        data, errors = self.extractData()
        self.theme_skel(data)

    
    def theme_skel(self,data):
        name = data.pop('name')
        data['namespace_package'],data['package'] = name.split('.')
        print "**" * 20,data['package'],name
        vars = ['%s=%s' % (k, v) for k,v in data.items()]
        print vars
        create.run([
                '--no-interactive',
                '--output-dir',
                output_dir,
                '-t',
                'plone3_theme',
                name,] + vars)
        # not sure why, but an unnecessary 'example' folder gets created
        # so we remove it after the theme is created
        

ThemeEditorExportView = wrap_form(ThemeEditorExportForm)

def _create_tpl():
    commands = get_commands()
    create = commands['create'].load()
    create=create('any name here')
    output_dir = tempfile.mkdtemp()
    tpl = zopeskel.plone3_theme.Plone3Theme("new template")
    return tpl,create,output_dir


