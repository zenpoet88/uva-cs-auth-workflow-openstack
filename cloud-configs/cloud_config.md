

# Configuraiton Documentation

## Top level items
 * `cloud_type` - string.  The backend type used for creating an enterprise.  Must be one of "openstack".

 * `os_env_file` - string.  The full path to a file that sets the environment to be able to access an openstack project.  
This file is `source`d (i.e., ran in the current shell) to set the environment.  It can just set env variables (prefered)
or prompt the user for things like passwords (less preferred), etc.

 * `private_key_file` - string.  The path to the private key used in keypair (as listed below).

 * `external_network` - string.  The openstack network that can access the outside world.  This also is the default network
access point for any deployed nodes.

 * `keypair` - string. The openstack keypair to be installed in the node.

 * `image_map` - object.  This object maps high-level image types to openstack image names.

 * `instance_size_map` - object.  This object maps high-level instance size names to openstack flavor names.

 * `security-group` - string. The security group to use when creating nodes.

 * `enterprise_url` - string.  The url for your enterprise that's used to create a domain.


##  Sub-fields


