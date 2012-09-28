from setuptools import setup, find_packages
import os

version = '1.0a6'

setup(name='plone.app.themeeditor',
      version=version,
      description="""Theme Editor for Plone, Customize your theme resources
through the web""",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "INSTALL.txt")).read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='theme editor customization plone',
      author='David Glick',
      author_email='davidglick@groundwire.org',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone', 'plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'five.customerize',
          'Paste',
          'PasteScript',
          'plone.app.customerize>=1.2',
          'plone.app.jquerytools>=1.3.1',
          'plone.app.z3cform>=0.5.0',
          'plone.memoize',
          'plone.portlets',
          'plone.z3cform',
          'Products.CMFCore',
          'Products.CMFFormController',
          'Products.GenericSetup',
          'setuptools',
          'templer.localcommands',
          'templer.plone', #Indirect requirement
          'z3c.form',
          'zc.buildout',
          'ZODB3', #Provides persistent
          'zope.app.component',
          'zope.component',
          'zope.i18n',
          'zope.i18nmessageid',
          'zope.interface',
          'zope.pagetemplate',
          'zope.publisher',
          'zope.schema>=3.6.0',
          'zope.viewlet',
          'Zope2', #Provides OFS, Products.Five, Testing
      ],
      extras_require={
          'test': ['niteoweb.windmill', 'Products.PloneTestCase',
            'plone.app.portlets', 'Acquisition'],
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
