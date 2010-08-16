# -*- coding: utf-8 -*-

from z3c.form import validator
from z3c.form.interfaces import IValidator
from zope.component import adapts
from plone.app.themeeditor.browser.export import IThemeEditorExportForm
from zope.interface import implements, Interface, Invalid

class DottedNameValidator(validator.SimpleFieldValidator):
    implements(IValidator)
    adapts(Interface, IThemeEditorExportForm)

    def validate(self, value):
        super(DottedNameValidator, self).validate(value)


        names = value.split(".")
        if len(names) < 2:
            raise Invalid('''Not a valid theme name. There are no dots, the theme name must have a single dot
                        separating two words e.g. "plonetheme.mytheme".''')
        if len(names) > 2:
            raise Invalid('''Not a valid dotted theme name. There
                        should be no more than one dot in the theme name
                        separating two words e.g. "plonetheme.mytheme".''')

        for name in names:
            # Check if Python identifier,
            # http://code.activestate.com/recipes/413487/
            try:
                class test(object): __slots__ = [name]
            except TypeError:
                raise Invalid('''Not a valid dotted theme name. %s
                                        should be a simple word with no special
                                        characters
                                       e.g. "plonetheme.mytheme".''' %  name)
            return True

# Register DottedName validator for the name field in the IThemeEditorExportForm
validator.WidgetValidatorDiscriminators(DottedNameValidator,
                                        field=IThemeEditorExportForm['name'])
