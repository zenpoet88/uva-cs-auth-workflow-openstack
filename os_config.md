

# Configuraiton Documentation

## Top level items

 * `os_env_file` - string.  The full path to a file that sets the environment to be able to access an openstack project.  
This file is `source`d (i.e., ran in the current shell) to set the environment.  It can just set env variables (prefered)
or prompt the user for things like passwords (less preferred), etc.


* `nodes` - array of node.  The list of nodes to be allocated.  See subfield `node`.


##  Sub-fields

* `node` - object.  Required subfields a `name` subfield and an `os` subfield that specify the name and os, respectively.  Optional subfield `domain` specifies
the windows domain that the machine should join.

* `name` - string.  THe name of an object.

* `os` - string. The name of an os, must be one of `win2k22`, `jammy`.

* `domain` - string. The name of the Windows domain that the node should join.



