

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client as keystone_client
from novaclient import client as nova_client


class OpenstackCloud:

    def __init__(self, cloud_config):
        self.sess = get_session()

    def get_session():
        """Return keystone session"""

        # Extract environment variables set when sourcing the openstack RC file.
        user_domain = os.environ.get('OS_USER_DOMAIN_NAME')
        user = os.environ.get('OS_USERNAME')
        password = os.environ.get('OS_PASSWORD')
        project_id = os.environ.get('OS_PROJECT_ID')
        auth_url = os.environ.get('OS_AUTH_URL')

        # Create user / password based authentication method.
        # https://goo.gl/VxD2FQ
        auth = v3.Password(user_domain_name=user_domain,
                           username=user,
                           password=password,
                           project_id=project_id,
                           auth_url=auth_url)

        # Create OpenStack keystoneauth1 session.
        # https://goo.gl/BE7YMt
        sess =  session.Session(auth=auth)
        print("Openstack session created.")
        return sess


