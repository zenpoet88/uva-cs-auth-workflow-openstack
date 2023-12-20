import time
import socket
import paramiko
from shell_handler import ShellHandler
from password import generate_password


domain_safe_mode_password = generate_password(12)
verbose = False

def deploy_forest(cloud_config,name,ipv4_addr,password,domain):

    user='Administrator'
    domain_name = domain + '.' + cloud_config['enterprise_url'] 

    cmd=(
        'Install-windowsfeature AD-domain-services ; '
        'Import-Module ADDSDeployment ;  '
        '$secure=ConvertTo-SecureString -asplaintext -string {} -force ; '
        'Install-ADDSForest -domainname {} -SafeModeAdministratorPassword $secure -verbose -NoRebootOnCompletion:$true -Force:$true  '
        ).format( domain_safe_mode_password,domain_name)


    if verbose:
        print("  Register forest command:" + cmd)

    shell = ShellHandler(ipv4_addr,user,password)
    stdout,stderr,exit_status = shell.execute_powershell(cmd, verbose=verbose)
    try:
        shell.execute_powershell('Restart-computer -force', verbose=verbose)
    except socket.error:
        pass

    print("  Waiting for reboot (Expect socket closed by peer messages).")
    time.sleep(10)
    status_received = False
    while not status_received:
        try:
            shell = ShellHandler(ipv4_addr,user,password)
            stdout2,stderr2,exit_status2 = shell.execute_powershell("get-addomain", verbose=verbose)
            if 'Attempting to perform the' in str(stdout2): 
                # server is starting up, try again.
                status_received=False
            else:
                status_received=True
        except paramiko.ssh_exception.SSHException:
            pass
        except paramiko.ssh_exception.NoValidConnectionsError:
            pass

    if not 'ReplicaDirectoryServers' in str(stdout2):
        print("Stdout2: " + str(stdout2))
        print("Stderr2: " + str(stderr2))
        errstr = 'Cannot get domain information from ' + name
        raise RuntimeError(errstr)

    print("  Reboot Complete.  Waiting for domain controller service to start.");
    # wait for domain controller to be up/ready.

    return {
                "deploy_forest_results": {"name": name, "addr":ipv4_addr, "password": password, "domain": domain }, 
                "install_forest": {"stdout": stdout, "stderr": stderr, "exit_status": exit_status},
                "verify_forest": {"stdout": stdout2, "stderr": stderr2, "exit_status": exit_status2},
                "domain_safe_mode_password": domain_safe_mode_password
            }


def add_domain_controller(cloud_config,leader_details,name,ipv4_addr,password,domain):
    user='Administrator'
    domain_name = domain + '.' + cloud_config['enterprise_url'] 
    leader_admin_password=leader_details['admin_pass']
    leader_ip=leader_details['addr']
    print('  domain-controller leader: ' + leader_ip)
    print('  domain-controller password: ' + leader_admin_password)

    cmd=(
        "Install-windowsfeature AD-domain-services ; "
        "Import-Module ADDSDeployment ;  "
        "Set-DnsClientServerAddress -serveraddress ('{}') -interfacealias 'Ethernet Instance 0' ; "
        "$passwd = convertto-securestring -AsPlainText -Force -String '{}' ; "
        "$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist '{}\\administrator',$passwd ; "
        "$secure=ConvertTo-SecureString -asplaintext -string '{}' -force ; "
        "Install-ADDSDomainController -DomainName {} -SafeModeAdministratorPassword $secure -verbose -NoRebootOnCompletion:$true  -confirm:$false -credential $cred"
        ).format( leader_ip, leader_admin_password, domain_name, domain_safe_mode_password,domain_name)


    if verbose:
        print("  Register as domain comtroller command:" + cmd)

    shell = ShellHandler(ipv4_addr,user,password)
    stdout,stderr,exit_status = shell.execute_powershell(cmd,verbose=verbose)

    try:
        shell = ShellHandler(ipv4_addr,user,password)
        shell.execute_powershell('Restart-computer -force', verbose=verbose)
    except socket.error:
        pass

    print("  Waiting for reboot (Expect socket closed by peer messages).")
    time.sleep(10)
    status_received = False
    while not status_received:
        try:
            shell = ShellHandler(ipv4_addr,user,leader_admin_password)
            stdout2,stderr2,exit_status2 = shell.execute_powershell("get-addomain", verbose=verbose)
            status_received=True
        except paramiko.ssh_exception.SSHException:
            pass
        except paramiko.ssh_exception.NoValidConnectionsError:
            pass

    if not 'ReplicaDirectoryServers' in str(stdout2):
        print("add-dc-stdout:" + str(stdout))
        print("add-dc-stderr:" + str(stderr))
        print("verify-stdout:" + str(stdout2))
        print("verify-stderr:" + str(stderr2))
        errstr = 'Cannot get domain information from ' + name
        raise RuntimeError(errstr)

    print("  Reboot Complete");

    return {
                "add_domain_results": {"name": name, "addr":ipv4_addr, "password": password, "domain": domain }, 
                "install_domain_controller": {"stdout": stdout, "stderr": stderr, "exit_status": exit_status},
                "verify_domain_controller": {"stdout": stdout2, "stderr": stderr2, "exit_status": exit_status2}
            }


def join_domain(obj):
    ret={}
    node=obj['node']
    name=node['name']
    leader=obj['domain_leader']
    addr=obj['addr']
    password=obj['password']
    roles=node['roles']
    iswindows = len(list(filter(lambda role: 'windows' == role, roles))) == 0
    islinux = len(list(filter(lambda role: 'linux' == role, roles))) == 0

    if iswindows:
        print("  Windows join-domain for node " + name)
    elif islinux:
        print("  Linux join-domain for node " + name)
    else:
        print("  No endpoint/domain enrollment for node " + name)

    return ret

    


