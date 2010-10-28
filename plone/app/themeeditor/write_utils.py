##############################################################################
#
# This code is borrowed from the qPloneSkinDump Product
# They apparently borrowed from a product called RedPICK 
# (Plone Intranet Construction Kit) 
#
##############################################################################
"""Skin dump Write Utilities
"""
#
# Main part of code of this module is taking from RedPICK product
# was made some correction in ControllerBaseMetadata forming procedure
#
import sys

def writeObjectsMeta( obj_meta, basepath ):
    "Write pairs list of object's id and his meta_type for given directory."
    data = ""
    for id, m_t in obj_meta.items():
        data += "%s : %s\n" % (id, m_t)
    filename = "%s/.objects" % basepath
    filewrite( filename, data )

# just in case of nessecity (not use now)
def writeProps( obj, basepath, extension = '.properties' ):
    "Write object properties to a file."
    ext = getExtForObject( obj )
    filename = basepath + '/' + obj.getId() + ext + extension
    writeProps2( filename, obj )

def writeFileContent( obj, basepath, data ):
    "Write object content to external file."
    ext = getExtForObject( obj )
    filename = basepath + '/' + obj.getId() + ext
    filewrite( filename, data, 'wb' )
    if 'Controller ' == obj.meta_type[:11]:
        _writeControllerBaseMetadata( obj, filename + '.metadata' )

def getExtForObject( obj ):
    "Return the appropriate filename extension according to the object meta_type."
    dict = {
        'Controller Page Template' : '.cpt',
        'Controller Python Script' : '.cpy',
        'Controller Validator' : '.vpy',
        'DTML Method' : '.dtml',
        #'File' : '',
        #'Folder' : '',
        #'Image' : '',
        'Page Template' : '.pt',
        'Script (Python)' : '.py',
        'I18NLayer' : '.I18NL',
    }
    return dict.get( obj.meta_type, '' )

def writeProps2( filename, obj ):
    "Write object properties to a file."
    filewrite( filename, formatProps2( obj ) )

def formatProps2( obj, notuple = 0, suppresstitle = 0, onlynew = None, existing = None ):
    "Return object properties in a multi-line string."
    lines = []
    props = obj.propertyMap()
    for prop in props:
        id = prop['id']
        tp = prop['type']
        if id.lower() == 'title' and suppresstitle:
            continue
        if onlynew and id in existing:
            continue
        value = obj.getProperty( id )
        if notuple:
            t = type( value )
            if t == type([]) or t == type(()):
                # we use comma as field delimiter, so be careful to escape existing ones
                value = map( lambda x: x.replace( ',', '&COMMA&' ), value )
                value = ','.join( list( value ) )
        #if this is a multiline string we must handle it specially
        #lines.append( '%s:%s=%s' % (id, tp, escape_quote( str( value ) ) ) )
        lines.append( '%s:%s=%s' % (id, tp, str( value ) ) )
    lines.sort()
    return '\n'.join( lines )

#def escape_quote( s ):
#    "Return string with all single and double quotes escaped, i.e. backslash added before."
#    return s.replace( '"', r'\"' ).replace( "'", r"\'" )

def _writeControllerBaseMetadata( obj, filename ):
    "Write controller base metadata to external file."
    lines = []
    if hasattr( obj, 'actions' ):
        for a in obj.actions.actions.values(): 
            lines.append(replaceActionKey(adjustMetadata(str( a ) ) ) )
        if lines: lines.insert( 0, '[actions]' )
    if hasattr( obj, 'validators' ):
        n = len( lines )
        for a in obj.validators.validators.values(): append_validator_str( lines, a )
        if len( lines ) > n: lines.insert( n, '[validators]' )
    if lines:
        # brauchts das ?? for a in lines: print a
        filewritelines( filename, lines )

def append_validator_str( lines, validator ):
    "Return a FormValidator string representation."
    #assert 'FormValidator' == validator.__class__, 'expected a FormValidator, not ' + str( validator )
    # validators.context.button = validate_script1, validate_script3
    vallist = ','.join( validator.getValidators() )
    if vallist:
        lines.append(adjustMetadata( 'validators.%s.%s=%s' \
            % (validator.getContextType(), validator.getButton(), vallist) ) )

def replaceActionKey(str):
    return "action.%s" % '.'.join(str.split(".")[1:])
    
def adjustMetadata(str):
    str = str.replace('.None', '.')
    while str.find('.=')>-1:
        str = str.replace('.=', '=')
    return str

def filewrite( filename, data, mode = 'wb' ):
    f = open( filename, mode )
    print "*****",filename,"********"
    try:
        f.write( prepareData(data) )
    except TypeError:
        # XXX this is a quick fix need to check back here
        f.write( prepareData(data.data) )
    f.close()

def filewritelines( filename, data ):
    "Write a list of strings to a file, joining list items with '\n'."
    f = open( filename, 'wb' )
    try:
        f.write( '\n'.join( [prepareData(item) for item in data]) )
    except:
        exc_type, exc_value, trace = sys.exc_info()
        raise Exception("There is %s (%s) exception while dumping %s file." % (exc_value, exc_type, filename))
    f.close()

def prepareData(data):
    """ Encode unicode type string for prevent UnicodeEncodeError 
        while writing none ascii string data to file."""
    return type(data) == type(u"") and data.encode("utf-8") or data
