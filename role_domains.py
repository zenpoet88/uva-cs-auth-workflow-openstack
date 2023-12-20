import time
import paramiko
from shell_handler import ShellHandler

def register_windows_instance(obj):
    ipv4_addr=obj['addr']
    password=obj['password']
    user='Administrator'
    cmd = 'slmgr.vbs /skms uvakms.eservices.virginia.edu; Start-Sleep -s 15; slmgr.vbs /ato; start-sleep -s 45; Get-CimInstance SoftwareLicensingProduct -Filter "Name like \'Windows%\'" | where { $_.PartialProductKey } | select Description, LicenseStatus'

    shell = ShellHandler(ipv4_addr,user,password)
    stdout,stderr,exit_status = shell.execute_powershell(cmd)

    return {"node_details": obj, "stdout": stdout, "stderr": stderr, "exit_status": exit_status}



domain_safe_mode_password = 'hello1!'

def deploy_forest(cloud_config,name,ipv4_addr,password,domain):

    user='Administrator'
    domain_name = domain + '.' + cloud_config['enterprise_url'] 

    cmd=(
        'Install-windowsfeature AD-domain-services ; '
        'Import-Module ADDSDeployment ;  '
        '$secure=ConvertTo-SecureString -asplaintext -string {} -force ; '
        'Install-ADDSForest -domainname {} -SafeModeAdministratorPassword $secure -verbose -NoRebootOnCompletion:$true -domainnetbiosname {} -Force:$true  '
        ).format( domain_safe_mode_password,domain_name,domain)


    print("  Register forest command:" + cmd)

    shell = ShellHandler(ipv4_addr,user,password)
    stdout,stderr,exit_status = shell.execute_powershell(cmd)
    try:
        shell.execute_powershell('Restart-computer -force')
    except socket.error:
        pass

    print("  Waiting for reboot (Expect socket closed by peer messages).")
    time.sleep(10)
    status_received = False
    while not status_received:
        try:
            shell = ShellHandler(ipv4_addr,user,password)
            stdout2,stderr2,exit_status2 = shell.execute_powershell("get-addomain")
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
        print("stdout:" + str(stdout2))
        print("stderr:" + str(stderr2))
        errstr = 'Cannot get domain information from ' + name
        raise RuntimeError(errstr)

    print("  Reboot Complete.  Waiting for domain controller service to start.");
    # wait for domain controller to be up/ready.
    time.sleep(60) 

    return {
                "deploy_forest_results": {"name": name, "addr":ipv4_addr, "password": password, "domain": domain }, 
                "install_forest": {"stdout": stdout, "stderr": stderr, "exit_status": exit_status},
                "verify_forest": {"stdout": stdout2, "stderr": stderr2, "exit_status": exit_status2}
            }


def add_domain_controller(cloud_config,leader_details,name,ipv4_addr,password,domain):
    user='Administrator'
    domain_name = domain + '.' + cloud_config['enterprise_url'] 
    leader_admin_password=leader_details['admin_pass']
    leader_ip=leader_details['addr']
    print('  domain-controller leader: ' + leader_ip)
    print('  domain-controller password: ' + leader_admin_password)

    cmd=(
        'Install-windowsfeature AD-domain-services ; '
        'Import-Module ADDSDeployment ;  '
        'Set-DnsClientServerAddress -serveraddress ("{}") -interfacealias "Ethernet Instance 0" ; '
        '$passwd = convertto-securestring -AsPlainText -Force -String "{}" ; '
        '$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist "{}\\administrator",$passwd ; '
        '$secure=ConvertTo-SecureString -asplaintext -string "{}" -force ; '
        'Install-ADDSDomainController -DomainName {} -SafeModeAdministratorPassword $secure -verbose -NoRebootOnCompletion:$true  -confirm:$false -credential $cred'
        ).format( leader_ip, leader_admin_password, domain, domain_safe_mode_password,domain_name)


    print("  Register as domain comtroller command:" + cmd)

    shell = ShellHandler(ipv4_addr,user,password)
    stdout,stderr,exit_status = shell.execute_powershell(cmd)
    print("add-dc-stdout:" + str(stdout))
    print("add-dc-stderr:" + str(stderr))
    try:
        shell.execute_powershell('Restart-computer -force')
    except socket.error:
        pass

    print("  Waiting for reboot (Expect socket closed by peer messages).")
    time.sleep(10)
    status_received = False
    while not status_received:
        try:
            shell = ShellHandler(ipv4_addr,user,leader_admin_password)
            stdout2,stderr2,exit_status2 = shell.execute_powershell("get-addomain")
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

