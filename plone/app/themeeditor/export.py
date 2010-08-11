from Products.CMFCore.utils import getToolByName
from zope.component import getUtility
from plone.app.themeeditor.interfaces import IResourceRetriever,IResourceType
from Products.GenericSetup.interfaces import IExportContext,IThemeExporter
from zope.interface import implements
from plone.memoize.instance import memoize
import tempfile
import logging
from StringIO import StringIO
from tarfile import TarFile

# get the message factory
from plone.app.themeeditor.interfaces import _


LOGGER="plone.app.themeeditor"

def info(msg):
    logging.getLogger(LOGGER).info(msg)

output_dir = tempfile.mkdtemp()

class TarballThemeExporter(object):

    implements(IThemeExporter)

    def export(self,export_context, subdir, root=False):
        """ Iterate over the customized_items and export using the API of 'export_context'. """
        # create a new theme using zopeskel

        # grab each resource and place in the new theme
        for resource in customized_resources:
            _export = self._export_method[resource.type]
            # use the export method
            _export(export_context)

    def customized_resources(self):
        """ Return a sequence of the customized items to be exported.
        rm = getUtility(IResourceRetriever)
        return list(rm.iter_resources(name=name,tags=['customized']))

    def set_options(self,**kwargs):
        """ set additional options for marshallers """

    def get_options(self):
        """ return set options """

    @property
    def _export_method(self):
        """ a convenience dictionary that returns the export method
            by resource type
        """
        resource_types = list(rm.iter_resource_types())
        res_export_method = {}
        for res_type in resource_types:
            res_export_method[res_type.name] = res_type.export
        return res_export_method

class TarballExportContext(object):
    """
    Export Data to Tarball
    This function is adapted from collective.plone.gsxml.context
    """
    implements(IExportContext)

    def __init__(self, fileobj=None, archive_name=None, mode="w:gz"):
        """
        inits the tar file
        """
        info( "TarballExportContext:__init__() fileobj=%s, archive_name=%s,
mode=%s" % (fileobj, archive_name, mode) )

        if archive_name is None:
            timestamp = time.gmtime()
            archive_name = ( 'themeeditor-%4d%02d%02d%02d%02d%02d.tar.gz'
                           % timestamp[:6] )
            info( "setting filename to %s" % archive_name )

        if fileobj is None:
            fileobj = StringIO()

        self.fileobj = fileobj
        self._archive_filename = archive_name
        self._archive = TarFile.open( archive_name, mode, fileobj )


    def writeDataFile(self, filename, text, content_type, subdir=output_dir):
        """
        See IExportContext
        """
        if subdir is not None:
            filename = '/'.join( ( subdir, filename ) )

        stream = StringIO( text )
        info = TarInfo( filename )
        info.size = len( text )
        info.mtime = time.time()
        self._archive.addfile( info, stream )

    def getArchive( self ):
        """ Close the archive, and return it as a big string.
        """
        self._archive.close()
        return self.fileobj.getvalue()

    def getArchiveStream( self ):
            """
            Returns a filelike object
            """
            self._archive.close()
            return self.fileobj

    def getArchiveFilename( self ):
        """
        Return the Filename of the Archive
        """
        return self._archive_filename

    def getArchiveSize(self):
        """
        Returns the length of the tar data
        """
        return len( self.fileobj.getvalue() )
