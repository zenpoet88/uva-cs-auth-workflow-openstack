# Workflows 

This tool helps setup and deploy an enterprise of compute nodes and users with various roles, domains, etc.
Also included is the ability to simulate workloads on the deployed infrastructure.

## Usage


### Site Configuration

Written in python and assumes to be running on Linux with ssh access to the nodes created, make sure you have dependencies setup properly:

```
$ ./setup.sh
$ pip install -r requirements.txt
```

The deploy scripts use [Designate](https://docs.openstack.org/designate/latest/) to handle DNS resolution, required for the Shibboleth workflow.  
Shibboleth and Moodle will not work without the proper DNS resolution.


### Infrastructure Setup

Then, you can deploy and configure an enterprise:

```
$ ./deploy-nodes.py cloud-configs/cloud-config.json enterprise-configs/enterprise-tiny.json
$ ./post-deploy.py deploy-output.json
```

This deploys the infrastructure, setups up domain controllers, etc.  Output is written to `deploy-output.json` and `post-deploy-output.json`.  
These files needs to be passed to later stages.
If `post-deploy-nodes.py` fails,  it is OK to re-run and see if the failure was temporary (e.g., a remote repository being unavailable or a network interference issue).

Some sample enterprises are included.  See [`enterprise.md`](./enterprise-configs/enterprise.md) for more details about these
files and how to create your own.

Sample cloud configurations are included (e.g., `mtx.json` and `shen.json`).  These are for
two Openstack deployments at UVA.  While this is setup to support any cloud infrastructure to deploy an enterprise,
only Openstack is currently supported.  See [`cloud-config.md`](./cloud-configs/cloud-config.md) for more details about writing
your own configuration.

To sanity check that your ssh keys and DNS are configured properly, you should be able to ping the various machines setup in your cloud config and enterprise config files, as well as ssh without a password into Linux VMs. 

For example, if the `enterprise_url` field in your cloud config is `castle.os`, and you have a Linux machine named `linep1` in your enterprise config,
you should be able to:

1. `ping linep1.castle.os`
2. `nslookup <name>.castle.os` # where *name* is any machine name defined in your enterprise config file
3. `ssh ubuntu@linep1.castle.os`

### Simulation

Next, you can generate logins for the deployed infrastrcuture:

```
$ ./simulate-logins.py  user-roles/user-roles.json enterprise-configs/enterprise-tiny.json
```

This generates users and estimates a login behavior for these users based on settings in the enterprise.json file
and user-roles.json file via a stocastic simulation.  
See additional details on the user-roles in [user-roles.md](./user-roles/user-roles.md).
Output is written to logins.json, used in later stages.

If you also want to emulate logins (next section), you will also need to install users into the enterprise.  You can do that by adding the enterprise description created when deploying the enterprise to the `simulate-logins` command.

```
$ ./simulate-logins.py  user-roles/user-roles.json enterprise-configs/web-wf.json post-deploy-output.json
```


### Emulation

Next, you can emulate the simulated logins:

```
$ ./emulate-logins.py  post-deploy-output.json logins.json 
```

If you want to do "fast" emulation for debugging, you can add the ``--fast-debug`` option.  You may also want to tell python not to buffer the output and redirect all output to a file:

```
$ python -u ./emulate-logins.py  post-deploy-output.json logins.json  --fast-debug 2>&1 |tee workflow.log
```



### Cleanup

Lastly, cleanup/destroy the infrastructure:

```
./cleanup-nodes.py output.json
```

Caution:  this destroy/deletes all nodes and infrastructures that were setup in prior steps.  Use with caution.


# Debugging

Most python scripts have a "verbose" variable near the top of the file.  
If you're having trouble with some aspect of the deployment, etc., you can try turning that on to see if verbose output 
is helpful with the problem.  Also, by default setup happens in parallel, and the post-deploy.py script has a `use_parallel`
option that can be used to do sequential setup, which far improves the ability to debug at the expense of significantly more
setup time.


# Deploying in Vanderbilt CAGE2 infrastructure.

* Run `deploy-nodes.py` and `post-deploy.py` to get a `post-deploy-output.json`.  
Use a enterprise configuration file that matches the VU deployment you wish to run the workflow on.
(E.g. cage2-ssh for the ssh workflow, or cage2-shib for the shib and Moodle workflows.)
Run `clean-nodes.py` to remove all nodes.

* Clone `git@github.com:CASTLEGym/castle-vm.git`.  

* Check out the `develop` branch, follow the README to deploy and provision the CAGE2 environment (including the UVA workflow stacks).
Make sure you follow the section at the end of the README about deploying workflows.

* Log into the "workflow" VM, and clone this repository.

* Copy the post-deploy-output.json from the first step to the workflow VM.  Modify it such that the addresses 
array matches the CAGE2 addresses assigned in the heat template. This modification can be done manually
by adding the control and game IPs to the addresses array in the JSON for each machine in the game.  
For cage2, this can be done with the convenience script called `convert-to-vu-cage2.py`.
```
cd /path/to/uva-workflows
./convert-to-vu-cage2.py ../../castle-vm/CreateVMs/VelociraptorVMs/secrets/castle-control
cd /path/to/castle-vm
ssh-keygen -f "/home/jdh8d/.ssh/known_hosts" -R "workflow.castle.os"
scp -i CreateVMs/VelociraptorVMs/secrets/castle-control CreateVMs/VelociraptorVMs/secrets/castle-control ubuntu@workflow.castle.os:~/.ssh
scp -i CreateVMs/VelociraptorVMs/secrets/castle-control ~/.ssh/id_rsa ubuntu@workflow.castle.os:~/.ssh
scp -i CreateVMs/VelociraptorVMs/secrets/castle-control ../uva_workflows/uva-cs-auth-workflow-openstack/deploy-output-vu-cage2.json ubuntu@workflow.castle.os:~/deploy-output.json 
ssh -i CreateVMs/VelociraptorVMs/secrets/castle-control ubuntu@workflow.castle.os
git clone git@github.com:jdhiser/uva-cs-auth-workflow-openstack.git workflow
mv deploy-output.json  workflow
cd workflow
git checkout -b pi_meeting_oct_2024
./setup.sh
mv ~/.ssh/castle-control ~/.ssh/id_rsa
./post-deploy.py deploy-output.json

```


* Set up DNS entries for the key machines (dc1.castle.os, service.castle.os, identity.castle.os).  DNS 
entries should point at the game addresses, not the control addresses.  
(TODO: Automate this leverage the the heat templates from the castle-vm repo.  
While I can do this with designate automatically, I'm not sure that works for VU yet.)

* Run post-deploy.py with the modified post-deploy-output.json to configure the HEAT-template deployed nodes.  

* Simulate and emulate logins from the workflow VM as per normal (described above).

# Debugging

It's python code, debug with your favorite debugger.  However, it's worth noting that 
most files have a "verbose" global variable so you can turn on verbose logging output 
for that file only.  Further, there is a `use_parallel` in the post-deploy script to 
sequentialize the deployment of nodes, which makes the verbose output much clearer.

Almost all input/output from remote machines is captured to the output file of every step.
You can load the output file into any JSON viewer (recommend something like Firefox)
and browse to output for each step.  These outputs can help diagnose connection issues,
etc.

