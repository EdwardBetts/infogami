"""Write query to create initial system objects including type system.
"""

# The bootstrap query will contain the following subqueries.
# 
# * create type/type without any properties
# * create all primitive types
# * create type/property and type/backreference
# * update type/type with its properties.
# * create type/user, type/usergroup and type/permission
# * create required usergroup and permission objects.

def _type(key, name, desc, properties=[], backreferences=[], kind='regular'):
    return dict(key=key, type={'key': '/type/type'}, name=name, desc=desc, kind=kind, properties=properties, backreferences=backreferences)

def _property(name, expected_type, unique=True, description='', **kw):
    return dict(kw, name=name, type={'key': '/type/property'}, expected_type={"key": expected_type}, unique={'type': '/type/boolean', 'value': unique}, description=description)
    
def _backreference(name, expected_type, property_name):
    pass

def primitive_types():
    """Subqueries to create all primitive types."""
    def f(key, name, description):
        return _type(key, name, description, kind='primitive')
    
    return [
        f('/type/key', 'Key', 'Type to store keys. A key is a string constrained to the regular expression [a-z][a-z/_]*.'),
        f('/type/string', 'String', 'Type to store unicode strings up to a maximum length of 2048.'),
        f('/type/text', 'Text', 'Type to store arbitrary long unicode text. Values of this type are not indexed.'),
        f('/type/int', 'Integer', 'Type to store 32-bit integers. This can store integers in the range [-2**32, 2**31-1].'),
        f('/type/boolean', 'Boolean', 'Type to store boolean values true and false.'),
        f('/type/float', 'Floating Point Number', 'Type to store 32-bit floating point numbers'),
        f('/type/datetime', 'Datetime', 'Type to store datetimes from 4713 BC to 5874897 AD with 1 millisecond resolution.'),
    ]
    
def system_types():
    return [
        _type('/type/property', 'Property', '', kind="embeddable",
            properties=[
                _property("name", "/type/string"),
                _property("expected_type", "/type/type"),
                _property("unique", "/type/boolean")
            ]
        ),
        _type('/type/backreference', 'Back-reference', '', kind='embeddable',
            properties=[
                _property("name", "/type/string"),
                _property("expected_type", "/type/type"),
                _property("property_name", "/type/string"),
                _property("query", "/type/string"),
            ]
        ),
        _type('/type/type', 'Type', 'Metatype.\nThis is the type of all types including it self.',
            properties=[
                _property("name", "/type/string"),
                _property("description", "/type/text"),
                _property("properties", "/type/property", unique=False),
                _property("backreference", "/type/backreference", unique=False),
                _property("kind", "/type/string", options=["primitive", "regular", "embeddable"], default="regular"),
            ]
        ),
        _type('/type/user', 'User', '',
            properties=[
                _property('displayname', '/type/string'),
                _property('website', '/type/string'),
                _property('description', '/type/text'),
            ]
        ),
        _type('/type/usergroup', 'Usergroup', '',
            properties = [
                _property('description', '/type/text'),
                _property('members', '/type/user', unique=False)
            ]
        ),
        _type('/type/permission', 'Permission', '',
            properties = [
                _property('description', '/type/text'),
                _property('readers', '/type/usergroup', unique=False),
                _property('writers', '/type/usergroup', unique=False),
                _property('admins', '/type/usergroup', unique=False),
            ]
        ),
        _type('/type/object', 'Object', 'placeholder type for storing arbitrary objects'),
        _type('/type/dict', 'Dict', 'placeholder type for storing arbitrary dictionaties', kind='embeddable'),
        _type('/type/delete', 'Deleted object', 'Type to mark an object as deleted.'),
        _type('/type/redirect', 'Redirect', 'Type to specify redirects.',
            properties = [
                _property('location', '/type/string'),
            ],        
        ),
    ]

def system_objects():
    def group(key, description):
        return {
            'key': key,
            'type': {'key': '/type/usergroup'},
            'description': description
        }
    
    def permission(key, readers, writers, admins):
        return {
            'key': key,
            'type': {'key': '/type/permission'},
            'readers': readers,
            'writers': writers,
            'admins': admins
        }
        
    def t(key):
        return {'key': key}
    
    return [
        group('/usergroup/everyone', 'Group of all users including anonymous users.'),
        group('/usergroup/allusers', 'Group of all registred users.'),
        group('/usergroup/admin', 'Group of admin users.'),
        permission('/permission/open', [t('/usergroup/everyone')], [t('/usergroup/everyone')], [t('/usergroup/admin')]),
        permission('/permission/restricted', [t('/usergroup/everyone')], [t('/usergroup/admin')], [t('/usergroup/admin')]),
        permission('/permission/secret', [t('/usergroup/admin')], [t('/usergroup/admin')], [t('/usergroup/admin')]),
    ]
    
def make_query():
    return primitive_types() + system_types() + system_objects()

def bootstrap(site, admin_password):
    """Creates system types and objects for a newly created site.
    """
    import cache
    cache.loadhook()
    
    import web
    web.ctx.infobase_bootstrap = True
    query = make_query()
    
    #site.write(query)
    site.save_many(query)
    a = site.get_account_manager()
    a.register(username="admin", email="admin@example.com", password=admin_password, data=dict(displayname="Administrator"))
    a.register(username="useradmin", email="useradmin@example.com", password=admin_password, data=dict(displayname="User Administrator"))
