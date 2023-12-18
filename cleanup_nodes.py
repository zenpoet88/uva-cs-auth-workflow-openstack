import sys
import json
from datetime import datetime
from openstack_cloud import OpenstackCloud


def load_output(output_filename):
    with open(output_filename) as f:
        # Read the file
        output = json.load(f)


    return cloud_config, enterprise

def cleanupy_enterprise(cloud_config,enterprise):
    ret = {}
    ret["cleanup_start"] = str(datetime.now());
    match cloud_config['cloud_type'].lower():
        case 'openstack':
           print("Using openstack cloud") 
           cloud =  OpenstackCloud(cloud_config)
        case _:
            print("Cannot find cloud type: " + cloud_config['cloud_type'])

    ret['cleanup'] = cloud.cleanup_enterprise(enterprise)

    ret["cleanup_end"] = str(datetime.now());
    return ret

def main():

    if len(sys.argv) != 2:
        print("Usage:  python " + sys.argv[0] + " cloud_config.json output.json ")
        sys.exit(1)

    cloud_config_filename = sys.argv[1]
    output_filename = sys.argv[2]
    json_output = load_output(output_filename)
    json_output["cleanup_start_time"] = str(datetime.now())
    cloud_config,enterprise = load_configs(cloud_config_filename, enterprise_filename)

    print("Cleaning up nodes.")
    cleanup_results = cleanup_enterprise(cloud_config,enterprise)
    print("Cleaning up, completed.")

    json_output['cleanup_backend_config'] = cloud_config;
    json_output['cleanup_results'] = cleanup_results;
    json_output["cleanupend_time"] = str(datetime.now())

    print("Enterprise cleaned.  Writing output to output.json.")
    with open("cleanup_output.json", "w") as f:
        json.dump(json_output,f)

    return


if __name__ == '__main__':
    main()

