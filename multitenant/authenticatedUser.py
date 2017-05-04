from multitenant.users import UserDescriptor, prepare_user
from multitenant.settings import multitenant_settings as settings
from multitenant.groups import list_groups


class AuthenticatedUser(UserDescriptor):

    def __init__(self, response):
        attrs = prepare_user(response)
        super(AuthenticatedUser, self).__init__(attrs)
        # server_conn, bind = server()
        # with Connection(server_conn, settings.ADMINISTRATOR, settings.PASSWORD, auto_bind=bind, client_strategy=REUSABLE) as conn:
        #     if self.is_owner:
        #         email = self.whoami.split(',')[0].partition('email=')[-1]
        #         search_filter = '(&(objectClass=' + settings.multitenantRootUserDescriptor + ')(email=' + email + '))'
        #         pool_counter = conn.search(self.whoami, search_filter, attributes=['*'])
        #         response, result = conn.get_response(pool_counter)
        #         user = list_users(response)
        #         self.attributes = user[0]  # can only have 1 user

    @property
    def whoami(self):
        return self.dn

    @property
    def is_authenticated(self):
        return True

    @property
    def is_owner(self):
        if self.whoami.startswith('uid'):
            return False
        return True

    @property
    def is_root(self):
        if 'root' in self.groups:
            return True
        return False

    #
    # @property
    # def groups(self):
    #     return self.groups
    #
    # @groups.setter
    # def groups(self, group_attrs=None):
    #     # if self.is_owner:
    #     #     self.__groups = settings.TENANT_GROUPS
    #
    #     # else:
    #     #     if group_attrs is None:
    #     #         raise Exception('Group attributes is empty.')
    #     #     groups = list_groups(group_attrs)
    #     #     self.__groups = groups
    #     pass

    def has_group(self, group_name):
        # """
        # at user creation lower groups are automatically assigned to user.
        # if admin, automatically has
        # if superuser, has admin
        # if root has all.
        # :param group_name: a str of group name
        # :return:
        # """
        # for group in self.groups:
        #     if group.name == group_name:
        #         return True
        # return False
        pass


class Authenticated(object):

    def __init__(self):
        self.__user = None

    @property
    def user(self):
        return self.__user

    @user.setter
    def user(self, response):
        self.__user = AuthenticatedUser(response)


authenticated = Authenticated()
