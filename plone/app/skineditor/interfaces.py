from zope.interface import Attribute
from zope.interface import Interface
from zope import schema

class IResourceRegistration(Interface):
    """ Represents the registration of a resource for a particular layer. """
    
    title = Attribute(u'User-oriented layer identifier')
    info = Attribute(u'Additional info about this resource.')
    
    layer = Attribute(u'The identifier of the layer for which this resource is registered.')
    active = Attribute(u'Boolean indicating whether this is the topmost layer.')
    actions = Attribute(u'List of (label, url) tuples for actions that can be performed on this registration.')

class IResource(Interface):
    """ Represents a named resource. A resource may have registrations on
    multiple layers. Only the one for the topmost layer is active.
    """
    
    title = Attribute(u'User-oriented resource name')
    description = Attribute(u"User-oriented clarification of this resource's type and context.")

    name = Attribute(u'Internal resource name')
    type = Attribute(u'The resource type of this resource')
    context = Attribute(u'The context interface for which this resource is registered.')
    
    registrations = schema.List(title=u'Registrations for this resource for different layers.',
                                value_type=schema.Object(schema=IResourceRegistration))

class IResourceType(Interface):
    
    name = Attribute(u'Name of this resource type')
    precedence = Attribute(u'Precedence of this resource type relative to others. '
                           u'Lower numbers equal higher precedence.')
    
    def __iter__():
        """ Returns an iterator enumerating the resources of this type. """
    
    def __getitem__(id):
        """ Return a resource by id. """
    
    def export(context):
        """ Exports TTW-customized resources to an export context. """

class IResourceRetriever(Interface):
    """ A resource retriever that can filter resources of different types. """
    
    def iter_resource_types():
        """ Returns an iterator of known resource types, in order of precedence. """
    
    def iter_resources(name=None, type=None, context=None):
        """ Returns an iterator of resources, filtered by the supplied criteria. """

class IResourceCustomizeForm(Interface):
    pass

class IResourceEditForm(Interface):
    pass
