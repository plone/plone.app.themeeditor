from zope.interface import Attribute
from zope.interface import Interface
from zope.i18nmessageid import MessageFactory

_ = MessageFactory('plone.app.themeeditor')

class IResourceRegistration(Interface):
    """ Represents the registration of a resource for a particular layer. """
    
    name = Attribute(u'Internal resource name')
    type = Attribute(u'The resource type of this resource')
    description = Attribute(u"User-oriented clarification of this resource's type and context")
    info = Attribute(u'Additional details about this resource.')
    
    path = Attribute(u'The path to the resource (on the filesystem or in the ZMI)')
    context = Attribute(u'The context interface for which this resource is registered.')
    layer = Attribute(u'The identifier of the layer for which this resource is registered.')
    actions = Attribute(u'List of (label, url) tuples for actions that can be performed on this registration.')
    tags = Attribute(u'List of arbitrary tags applying to this resource.')

    icon = Attribute(u'The path to the icon of the object.')

class IResourceType(Interface):
    
    name = Attribute(u'Name of this resource type')
    
    def __iter__():
        """ Returns an iterator enumerating the resources of this type. """
    
    def export(context):
        """ Exports TTW-customized resources to an export context. """

class IResourceRetriever(Interface):
    """ A resource retriever that can filter resources of different types. """
    
    def iter_resource_types():
        """ Returns an iterator of known resource types. """
    
    def iter_resources(name=None, type=None, context=None, tags=None):
        """ Returns an iterator of lists of resource registrations grouped by name.
        
        Results are filtered by the supplied criteria and ordered by name.
        """

class IResourceCustomizeForm(Interface):
    pass

class IResourceEditForm(Interface):
    pass
