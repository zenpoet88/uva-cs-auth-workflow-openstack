

# Configuraiton Documentation

## Top level items

`os_env_file` - string.  The full path to a file that sets the environment to be able to access an openstack project.  
This file is `source`d (i.e., ran in the current shell) to set the environment.  It can just set env variables (prefered)
or prompt the user for things like passwords (less preferred), etc.
