
import os


from keystoneauth1.exceptions import catalog
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client as keystone_client
from novaclient import client as nova_client
from collections import defaultdict




class OpenstackCloud:

    def __init__(self, cloud_config):
        self.cloud_config = cloud_config
        self.sess = OpenstackCloud.get_session()
        self.nova_sess = nova_client.Client(version=2, session=self.sess)
        self.servers = OpenstackCloud.query_servers(self.nova_sess)

        print(self.servers)


    def get_session():
        """Return keystone session"""

        # Extract environment variables set when sourcing the openstack RC file.
        user_domain = os.environ.get('OS_USER_DOMAIN_NAME')
        user = os.environ.get('OS_USERNAME')
        password = os.environ.get('OS_PASSWORD')
        project_id = os.environ.get('OS_PROJECT_ID')
        auth_url = os.environ.get('OS_AUTH_URL')
        domain_name = os.environ.get('OS_PROJECT_DOMAIN_NAME')

        # Create user / password based authentication method.
        # https://goo.gl/VxD2FQ
        auth = v3.Password(user_domain_name=user_domain,
                           username=user,
                           password=password,
                           project_id=project_id,
                           auth_url=auth_url)

        # Create OpenStack keystoneauth1 session.
        # https://goo.gl/BE7YMt
        sess = session.Session(auth=auth)

        return sess

    def query_servers(nova_sess):
        """Query list of servers.
        Returns a dictionary of server dictionaries with the key being the
        server name
        """
        servers = defaultdict()
        nova_servers = nova_sess.servers.list()
        print(nova_servers)

        for idx, server in enumerate(nova_servers):
            print("Found servers")
            server_dict = server.to_dict()
            servers[server.human_id] = server_dict
            print('server= '+ str(server_dict))
        return servers


    def check_deploy_ok(self,enterprise):
        for node in enterprise['nodes']:
            to_deploy_name = node['name']
            for instance_key in self.servers:
                instance_name=self.servers[instance_key]['name']
                print("comparing " + to_deploy_name + " to " + instance_name )
                if to_deploy_name.strip() == instance_name.strip():
                    return False;
        return True


    def deploy_enterprise(self,enterprise):
        ret = {} 
        ret['nodes']=[]

        ret['check_deploy_ok'] = self.check_deploy_ok(enterprise)
        if not ret['check_deploy_ok']:
            return  ret

        for node in enterprise['nodes']:
            name = node['name']
            os_name = node['os']
            size = node.get('size', "small")
            domain = node.get('domain',"")

            image = OpenstackCloud.os_to_image(os_name);
            flavor = OpenstackCloud.size_to_falvor(os_name);

            new_node = {}
            new_node['name'] = name;
            new_node['flavor'] = flavor;
            new_node['size'] = size;
            new_node['os'] = os_name;
            new_node['domain'] = domain;
            new_node['image'] = image;
            ret['nodes'].append(new_node)

        return ret


    def os_to_image(size):
        return self.cloud_config['image_map'][os_name]

    def size_to_flavor(self,size_name):
        return self.cloud_config['instance_size_map'].get(size,"m1.small")
