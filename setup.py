from setuptools import setup, find_packages
import os

version = '1.0a3'

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
      namespace_packages=['plone'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'five.customerize',
          'Paste',
          'PasteScript',
          'Products.CMFCore',
          'plone.app.customerize>=1.2',
          'plone.app.jquerytools>=1.1b6',
          'plone.app.z3cform>=0.5.0',
          'plone.memoize',
          'setuptools',
          'zope.component',
          'ZopeSkel>=2.17',
          'zope.app.component',
          'zope.interface',
          'zope.schema>=3.6.0',
          'Zope2',
          'ZODB3',
      ],
      extras_require = {
          'test': ['niteoweb.windmill',],
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
