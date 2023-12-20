

# Configuraiton Documentation

## Top level items

 * `os_env_file` - string.  The full path to a file that sets the environment to be able to access an openstack project.  
This file is `source`d (i.e., ran in the current shell) to set the environment.  It can just set env variables (prefered)
or prompt the user for things like passwords (less preferred), etc.


* `nodes` - array of node.  The list of nodes to be allocated.  See subfield `node`.


##  Sub-fields

* `node` - object.  Subfields are:
**  a `name` - string.The name of the node. (required)
** an `os` - string. Specify the os to use. (required)
** `domain` - string. the windows domain that the machine should join, or no domain if the file is empty. (optional)
** `size` - string. the size of an instance.

* `name` - string.  THe name of an object.

* `os` - string. The name of an os, must be one of `win2k22`, `jammy`.

* `domain` - string. The name of the Windows domain that the node should join.

* 'size' - string. The size of parent opbject.

* `roles` - array of string.  The roles this machine should play.  
** `windows` -- register the instance with skms.  Specifies logins should be via password.
** `domain_controller_leader` -- install a domain controller with a new forest for active directory.
** `domain_controller` -- join an existing domain (requires a domain_controller_leader.
** `linux` -- specifies login should be via ssh key.



