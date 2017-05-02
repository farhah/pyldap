from __future__ import unicode_literals
from multitenant.settings import multitenant_settings as settings
from ldap3 import Server, Connection, Tls, AUTO_BIND_TLS_BEFORE_BIND, AUTO_BIND_NO_TLS, LDAPException, REUSABLE, ALL
import ssl
from multitenant.authenticatedUser import authenticated
from contextlib import contextmanager

import logging
from ldap3.utils.log import set_library_log_detail_level, EXTENDED


# def tls():
#     t = Tls(local_private_key_file=settings.LOCAL_PRIVATE_KEY_FILE,
#             local_certificate_file=settings.LOCAL_CERTIFICATE_KEY_FILE,
#             validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1,
#             ca_certs_file=settings.CA_CERTS_FILE)
#     return t
#
#
# def server():
#     tls_ = getattr(settings, 'TLS', None)
#     if tls_:
#         tls_ = tls()
#         bind_conn = AUTO_BIND_TLS_BEFORE_BIND
#     else:
#         bind_conn = AUTO_BIND_NO_TLS
#
#     server_conn = Server(settings.LDAP_SERVER, settings.PORT, tls=tls_, get_info=ALL)
#     return server_conn, bind_conn


# @contextmanager
# def connect_ldap(username, password):
#     tls_ = getattr(settings, 'TLS', None)
#
#     if tls_:
#         tls_ = tls()
#         bind = AUTO_BIND_TLS_BEFORE_BIND
#     else:
#         bind = AUTO_BIND_NO_TLS
#
#     server = Server(settings.LDAP_SERVER, settings.PORT, tls=tls_, get_info=ALL)
#     conn = Connection(server, username, password, auto_bind=bind, client_strategy=REUSABLE, pool_name='multitenant_ldap_pool')
#     try:
#         yield conn
#     finally:
#         conn.unbind()


def operation(op):

    def wrap(func):
        def wrapped_func(*args, **kwargs):
            func(*args, **kwargs)
            operations = ['add', 'delete', 'modify', 'modify_dn', 'search']
            op_ = op if op in operations else None
            server_conn, bind = ConnectLDAP.server()

            if not op_:
                raise Exception("Connection operation is not recognized: {}".format(op))

            # with Connection(server_conn, settings.ADMINISTRATOR, settings.PASSWORD,
            #                 auto_bind=bind, client_strategy=REUSABLE) as conn:
            #     print(conn)
            #     del kwargs['requested_user']
            #     operation_ = getattr(conn, op_)
            #     args = args[1:]  # remove self
            #     # operation_(*args, **kwargs)
            #     pool_counter = operation_(*args, **kwargs)
            #     response, result = conn.get_response(pool_counter)
            #     # response = conn.response
            #     # result = conn.result
            #     return {'response': response, 'result': result}

            conn = Connection(server_conn, settings.ADMINISTRATOR, settings.PASSWORD, auto_bind=bind)
            # del kwargs['requested_user']
            operation_ = getattr(conn, op_)
            args = args[1:]  # remove self
            operation_(*args, **kwargs)
            # pool_counter = operation_(*args, **kwargs)
            # response, result = conn.get_response(pool_counter)
            response = conn.response
            result = conn.result
            return {'response': response, 'result': result}

        return wrapped_func
    return wrap


class ConnectLDAP(object):

    def __init__(self):
        logging.basicConfig(filename='client_application.log', level=logging.DEBUG)
        set_library_log_detail_level(EXTENDED)

        if not hasattr(self, 'auth_user'):
            print('-----no user is authenticated yet.-----')

    @classmethod
    def server(cls):

        def tls():
            t = Tls(local_private_key_file=settings.LOCAL_PRIVATE_KEY_FILE,
                    local_certificate_file=settings.LOCAL_CERTIFICATE_KEY_FILE,
                    validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1,
                    ca_certs_file=settings.CA_CERTS_FILE)
            return t

        tls_ = getattr(settings, 'TLS', None)
        if tls_:
            tls_ = tls()
            bind_conn = AUTO_BIND_TLS_BEFORE_BIND
        else:
            bind_conn = AUTO_BIND_NO_TLS

        server_conn = Server(settings.LDAP_SERVER, settings.PORT, tls=tls_, get_info=ALL)
        return server_conn, bind_conn

    @operation('add')
    def test(self, dn, object_class=None, attributes=None, controls=None):
        if not getattr(self, 'auth_user'):
            raise Exception('User is not authenticated.')

    @operation('add')
    def add(self, dn, object_class=None, attributes=None, controls=None):
        pass

    @operation('delete')
    def delete(self, dn, controls=None):
        if not getattr(self, 'auth_user'):
            raise Exception('User is not authenticated.')

    @operation('modify')
    def modify(self, dn, changes, controls=None):
        if not getattr(self, 'auth_user'):
            raise Exception('User is not authenticated.')

    @operation('modify_dn')
    def modify_dn(self,
                  dn,
                  relative_dn,
                  delete_old_dn=True,
                  new_superior=None,
                  controls=None):
        if not getattr(self, 'auth_user'):
            raise Exception('User is not authenticated.')

    @operation('search')
    def search(self,
               search_base,
               search_filter,
               search_scope='SUBTREE',
               dereference_aliases='ALWAYS',
               attributes=None,
               size_limit=0,
               time_limit=0,
               types_only=False,
               get_operational_attributes=False,
               controls=None,
               paged_size=None,
               paged_criticality=False,
               paged_cookie=None):
        # test = getattr(self, 'auth_user', None)
        # print('4 --> {}'.format(test.user))
        # if not getattr(self, 'auth_user'):
        #     raise Exception('User is not authenticated.')
        pass

    def auth(self, user=None, password=None):

        def is_root(whoami):
            if whoami.startswith('uid'):
                return False
            return True

        server_conn, bind_conn = ConnectLDAP.server()

        with Connection(server_conn, user, password, auto_bind=bind_conn) as conn:
            whoami = conn.extend.standard.who_am_i()

            if not whoami:
                return None
            whoami = whoami.split('dn:')[1]

            user_type = is_root(whoami)
            if user_type:
                email = whoami.split(',')[0].partition('email=')[-1]
                search_filter = '(&(objectClass=' + settings.multitenantRootUserDescriptor + ')(email=' + email + '))'
                conn.search(whoami, search_filter, attributes=['*'])
                authenticated.user = conn.response
                authenticated.user.groups = 'all'
                if not authenticated.user.is_active:
                    return False
                setattr(self, 'auth_user', authenticated)
                return authenticated

        with Connection(server_conn, settings.ADMINISTRATOR, settings.PASSWORD, auto_bind=bind_conn) as conn:
            app_dn = 'applicationUUID' + whoami.partition('applicationUUID')[-1]
            uid = whoami.split(',')[0].partition('uid=')[-1]
            search_filter = '(&(objectClass=' + settings.multitenantUserDescriptor + ')(uid=' + uid + '))'
            conn.search(app_dn, search_filter, attributes=['*'])
            authenticated.user = conn.response
            print(dir(authenticated))
            if not authenticated.user.is_active:
                return False

            search_filter_group = '(&(objectClass=groupOfNames)(member=' + whoami + '))'
            conn.search(app_dn, search_filter_group, attributes=['*'])
            authenticated.user.groups = conn.response

            setattr(self, 'auth_user', authenticated)
            return authenticated

    def logout(self, conn):
        conn.unbind()


ldap = ConnectLDAP()



# import uuid
# conn_ = ConnectLDAP()
# email = 'miu@miu.com'
# uuid_ = uuid.uuid5(uuid.uuid4(), email)
# cn = 'email=miu@miu.com,ou=rootuser,ou=multitenant,dc=ldapserver,dc=io'
# attrs = {'userPassword': 'mypassword', 'isActive': 'TRUE', 'uuid': uuid_, 'email': email, 'cn': cn}
# dn = 'email=miu@miu.com,ou=rootuser,ou=multitenant,dc=ldapserver,dc=io'
# a = conn_.test(dn, 'multitenantRootUserDescriptor', attrs)
# # a = conn_.test(dn, object_class='multitenantRootUserDescriptor', attributes=attrs)
#
# print(a)
# # print(dir(conn_ldap))
# conn = conn_ldap.connect(settings.ADMINISTRATOR, settings.PASSWORD)
# print(conn)
# print(conn.result)
# print(conn.extend.standard.who_am_i())
# conn.add()
