import sys
import logging
import json
from datetime import date
import openstack_cloud


def load_configs(cloud_config_filename, enterprise_filename):
    with open(cloud_config_filename) as f:
        # Read the file
        cloud_config = json.load(f)

    with open(enterprise_filename) as f:
        # Read the file
        enterprise =  json.load(f)


    return cloud_config, enterprise

def deploy_nodes(cloud_config,enterprise):
    ret = {}
    ret["deploy_start"] = date.today();
    match cloud_config['cloud_type'].lower():
        case 'openstack':
           print("Using openstack cloud") 
           cloud =  OpenstackCloud(cloud_config)
        case _:
            print("Cannot find cloud type: " + cloud_config['cloud_type'])

    ret["deploy_end"] = date.today();
    return ret

def main():

    if len(sys.argv) != 3:
        print("Usage:  python " + sys.argv[0] + " cloud_config.json enterprise.json")
        sys.exit(1)

    json_output = {}
    json_output["start_time"] = date.today()
    cloud_config_filename = sys.argv[1]
    enterprise_filename  = sys.argv[2]
    cloud_config,enterprise = load_configs(cloud_config_filename, enterprise_filename)

    print("Deploying nodes.")
    enterprise_built = deploy_nodes(cloud_config,enterprise)
    print("Nodes deployed, writing to info to nodes.json");
    json_output['backend_config'] = cloud_config;
    json_output['enterprise_to_build'] = enterprise;
    json_output['enterprise_built'] = enterprise_built;
    json_output["end_time"] = date.today()

    with open("output.json", "w") as f:
        json.dump(json_output,f)

    return



if __name__ == '__main__':
    LOG = logging.getLogger(__name__)
    LOG.setLevel(logging.INFO)
    LOG.addHandler(logging.StreamHandler(sys.stdout))
    main()

