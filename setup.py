from setuptools import setup, find_packages
import os

version = '1.0a1'

setup(name='plone.app.themeeditor',
      version=version,
      description="",
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
          'Products.CMFCore',
          'plone.app.customerize>=1.2',
          'plone.app.jquerytools>=1.1b6',
          'plone.memoize',
          'setuptools',
          'zope.component',
          'zope.app.component',
          'zope.interface',
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
