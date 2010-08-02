from setuptools import setup, find_packages

version = '0.1dev'

setup(name='plone.app.themeeditor',
      version=version,
      description="",
      long_description=open("README.txt").read() + "\n" +
                       open("CHANGES.txt").read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='David Glick',
      author_email='davidglick@groundwire.org',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'collective.monkeypatcher',
          'five.customerize',
          'Products.CMFCore',
          'plone.app.customerize',
          'plone.app.jquerytools>=1.1b6',
          'plone.app.z3cform',
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
          'plone3': ['plone.app.customerize>=1.1.3',],
                       
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
