from .common import *

import os
import saml2

SAML_CREATE_UNKNOWN_USER = True
SAML_ATTRIBUTE_MAPPING = {
    'mail': ('username', 'email', ),
    'cn': ('first_name', ),
    'sn': ('last_name', ),
    'o': ('organization', ),
    'eduPersonAffiliation': ('groups', ),
}

SAML_CONFIG = {
    # full path to the xmlsec1 binary programm
    'xmlsec_binary': '/usr/bin/xmlsec1',

    # your entity id, usually your subdomain plus the url to the metadata view
    'entityid': 'http://moocng.devopenmooc.com/auth/saml2/metadata/',

    # directory with attribute mapping
    'attribute_map_dir': os.path.join(BASEDIR, 'attributemaps'),

    # this block states what services we provide
    'service': {
        # we are just a lonely SP
        'sp': {
            'name': 'Moocng SP',
            'endpoints': {
                # url and binding to the assetion consumer service view
                # do not change the binding or service name
                'assertion_consumer_service': [
                    ('http://moocng.devopenmooc.com/auth/saml2/acs/', saml2.BINDING_HTTP_POST),
                ],
                # url and binding to the single logout service view
                # do not change the binding or service name
                'single_logout_service': [
                    ('http://moocng.devopenmooc.com.geographica.gs/auth/saml2/ls/', saml2.BINDING_HTTP_REDIRECT),
                ],
            },

            # in this section the list of IdPs we talk to are defined
            'idp': {
                # we do not need a WAYF service since there is
                # only an IdP defined here. This IdP should be
                # present in our metadata

                # the keys of this dictionary are entity ids
                'https://idp.devopenmooc.com/simplesaml/saml2/idp/metadata.php': {
                    'single_sign_on_service': {
                        saml2.BINDING_HTTP_REDIRECT: 'https://idp.devopenmooc.com/simplesaml/saml2/idp/SSOService.php',
                    },
                    'single_logout_service': {
                        saml2.BINDING_HTTP_REDIRECT: 'https://idp.devopenmooc.com/simplesaml/saml2/idp/SingleLogoutService.php',
                    },
                },
            },
        },
    },

    # where the remote metadata is stored
    'metadata': {
        'local': [os.path.join(BASEDIR, 'remote_metadata.xml')],
    },

    # set to 1 to output debugging information
    'debug': 1,

    # certificate
    'key_file': os.path.join(BASEDIR, 'server.key'),  # private part
    'cert_file': os.path.join(BASEDIR, 'server.pem'),  # public part

    # own metadata settings
    'contact_person': [
        {'given_name': 'Sysadmin',
         'sur_name': '',
         'company': 'Example CO',
         'email_address': 'sysadmin@devopenmooc.com',
         'contact_type': 'technical'},
        {'given_name': 'Boss',
         'sur_name': '',
         'company': 'Example CO',
         'email_address': 'admin@devopenmooc.com',
         'contact_type': 'administrative'},
    ],
    # you can set multilanguage information here
    'organization': {
        'name': [('Example CO', 'es'), ('Example CO', 'en')],
        'display_name': [('DevOpenMOOC', 'es'), ('DevOpenMOOC', 'en')],
        'url': [('http://www.devopenmooc.com', 'es'), ('http://www.devopenmooc.com', 'en')],
    },
}
