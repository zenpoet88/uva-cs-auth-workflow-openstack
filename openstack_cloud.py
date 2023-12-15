
import os
import time
from keystoneauth1.exceptions import catalog
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client as keystone_client
from novaclient import client as nova_client
from collections import defaultdict
from neutronclient.v2_0 import client as neutronclient
import glanceclient




class OpenstackCloud:

    def __init__(self, cloud_config):
        self.cloud_config = cloud_config
        self.sess = OpenstackCloud.get_session()
        self.nova_sess = nova_client.Client(version=2, session=self.sess)
        self.servers = self.query_servers()
        self.glclient = glanceclient.Client(version=2, session=self.sess)
        self.neutronClient = neutronclient.Client(session=self.sess)

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

    def query_servers(self):
        """Query list of servers.
        Returns a dictionary of server dictionaries with the key being the
        server name
        """
        servers = defaultdict()
        nova_servers = self.nova_sess.servers.list()

        for idx, server in enumerate(nova_servers):
            server_dict = server.to_dict()
            servers[server.human_id] = server_dict
        return servers


    def check_deploy_ok(self,enterprise):
        for node in enterprise['nodes']:
            to_deploy_name = node['name']
            for instance_key in self.servers:
                instance_name=self.servers[instance_key]['name']
                if to_deploy_name.strip() == instance_name.strip():
                    print("Found that server " + instance_name + " already exists.")
                    return False;
        return True

    def os_to_image(self,os_name):
        return self.cloud_config['image_map'][os_name]

    def size_to_flavor(self,size_name):
        return self.cloud_config['instance_size_map'].get('size',"m1.small")

    def find_image_by_name(self,name):
        images = self.glclient.images.list()
        found_image = None
        for image in images:
            if image['name'] == name and found_image == None:
                found_image=image
            elif image['name'] == name and found_image != None:
                str="Duplicate images named " + name 
                raise NameError(str)
        if found_image == None:
            str="Image not found: " + name 
            raise NameError(str)
        print("Found image id: " + found_image['id'])
        return found_image

    def find_network_by_name(self,name):
        ret = self.neutronClient.list_networks(name=name)
        networks = ret['networks']
        found_network = None
        for network in networks:
            if network['name'] == name and found_network == None:
                found_network=network
            elif network['name'] == name and found_network != None:
                str="Duplicate networks named " + name 
                raise NameError(str)
        if found_network == None:
            str="Network not found: " + name 
            raise NameError(str)
        print("Found network id: " + found_network['id'])
        return found_network



    def deploy_enterprise(self,enterprise):
        ret = {} 
        ret['nodes']=[]

        ret['check_deploy_ok'] = self.check_deploy_ok(enterprise)
        if not ret['check_deploy_ok']:
            print("Found that one or more nodes already exist, aborting deploy.")
            return  ret

        for node in enterprise['nodes']:
            name = node['name']
            os_name = node['os']
            size = node.get('size', "small")
            domain = node.get('domain',"")
            keypair = self.cloud_config['keypair']

            image = self.os_to_image(os_name);
            flavor = self.size_to_flavor(os_name);
            security_group = self.cloud_config['security_group'];
            network = node.get('network',self.cloud_config['external_network']);

            nova_image = self.find_image_by_name(image);
            nova_flavor = self.nova_sess.flavors.find(name=flavor);
            nova_net = self.find_network_by_name(network)
            nova_nics = [{'net-id': nova_net['id']}]
            print("Creating server named " + name)
            nova_instance = self.nova_sess.servers.create(name=name, image=nova_image, flavor=nova_flavor, key_name=keypair, nics=nova_nics)
            time.sleep(5);
            print(" Server " + name + " has id " + nova_instance.id)
            nova_instance = self.nova_sess.servers.get(nova_instance.id)
            new_node = {}
            new_node['name'] = name;
            new_node['flavor'] = flavor;
            new_node['size'] = size;
            new_node['os'] = os_name;
            new_node['domain'] = domain;
            new_node['image'] = image;
            new_node['security_group'] = security_group;
            new_node['network'] = network;
            new_node['keypair'] = keypair;
            new_node['nova_image'] = nova_image;
            new_node['nova_flavor'] = nova_flavor;
            new_node['nova_nics'] = nova_nics;
            new_node['nova_instance'] = nova_instance;
            ret['nodes'].append(new_node)

        return ret



