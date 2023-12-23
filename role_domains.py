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
    print("Setting safe-mode password for domain to " + password)

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
    leader_ip=leader_details['addr'][0]
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
    cloud_config=obj['cloud_config']
    node=obj['node']
    name=node['name']
    domain_name=obj['domain']
    enterprise_name = cloud_config['enterprise_url'] 
    fqdn_domain_name = domain_name + '.' + enterprise_name; 
    leader=obj['domain_leader']
    leader_admin_password=leader['admin_pass']
    leader_addrs=leader['addr']
    ipv4_addr=obj['addr']
    password=obj['password']
    roles=node['roles']
    iswindows = len(list(filter(lambda role: 'windows' == role, roles))) == 1
    islinux = len(list(filter(lambda role: 'linux' == role, roles))) == 1

    # convert array into string for powershell.
    domain_ips = str(leader_addrs).replace("[","").replace(']','').replace("'",'"')


    if verbose:
        print("  Domain controller leader:" + leader['name'])
        print("  Domain controller IPs:" + str(leader_addrs))

    if iswindows:
        print("Windows join-domain for node " + name)
        return join_domain_windows(name, leader_admin_password, ipv4_addr, domain_ips, fqdn_domain_name, domain_name, password)
    elif islinux:
        print("Linux join-domain for node " + name)
        return join_domain_linux(name, leader_admin_password, ipv4_addr, domain_ips, fqdn_domain_name, domain_name, password, enterprise_name)
    else:
        errstr = "  No endpoint/domain enrollment for node " + name
        raise RuntimeError(errstr)


def join_domain_windows(name, leader_admin_password, ipv4_addr, domain_ips, fqdn_domain_name, domain_name, password):

    print("Windows join-domain for node " + name)

    user='Administrator'
    cmd=(
        "$passwd = convertto-securestring -AsPlainText -Force -String {} ; "
        "$cred = new-object -typename System.Management.Automation.PSCredential -argumentlist '{}\\administrator',$passwd ; "
        "Set-DnsClientServerAddress -serveraddress ({}) -interfacealias 'Ethernet Instance 0' ; "
        "Add-Computer -Credential $cred -domainname {}" 

        ).format(leader_admin_password, domain_name, domain_ips, fqdn_domain_name)


    print("  Joining an exsiting domain: " + domain_name)

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
            shell = ShellHandler(ipv4_addr,domain_name+'\\'+user,leader_admin_password)
            stdout2,stderr2,exit_status2 = shell.execute_powershell('echo "the domain is $env:userdomain" ', verbose=verbose)
            status_received=True
        except paramiko.ssh_exception.SSHException:
            pass
        except paramiko.ssh_exception.NoValidConnectionsError:
            pass
    print("  Reboot Completed by verifying computer is in the domain");
    if not 'the domain is {}'.format(domain_name.upper()) in str(stdout2):
        print("join_domain_stdout:" + str(stdout))
        print("join_domain_stderr:" + str(stderr))
        print("verify_domain_stdout:" + str(stdout2))
        print("verify_domain_stderr:" + str(stderr2))
        errstr = 'Cannot get domain information from ' + name
        raise RuntimeError(errstr)

    return {
                "join_domain": {"stdout": stdout, "stderr": stderr, "exit_status": exit_status},
                "verify_join_domain": {"stdout": stdout2, "stderr": stderr2, "exit_status": exit_status2}
            }

def join_domain_linux(name, leader_admin_password, ipv4_addr, domain_ips, fqdn_domain_name, domain_name, password, enterprise_name):
    netplan_config_path='/etc/netplan/50-cloud-init.yaml'
    chrony_config_path='/etc/chrony/chrony.conf'
    domain_ips_formated = str(domain_ips).replace('[','').replace(']','').replace('"','')
    krdb_config_path='/etc/krb5.conf'


    set_allow_password="sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/'  /etc/ssh/sshd_config"
    set_dns_command=(
        "sudo sed -i '/dhcp4: true/a \            nameservers:\\n                addresses: \[ {} \]' {} ;  "
        "sudo netplan apply "
        ).format(domain_ips_formated, netplan_config_path)

    install_packages_cmd="sudo apt update && sudo env DEBIAN_FRONTEND=noninteractive apt install -y chrony krb5-user realmd sssd sssd-tools adcli samba-common-bin"

    set_chrony_command=(
        "sudo sed -i '/pool ntp.ubuntu.com        iburst maxsources 4/i pool {}        iburst maxsources 5' {} ; "
        "sudo systemctl enable chrony ; "
        "sudo systemctl restart chrony "
        ).format(fqdn_domain_name, chrony_config_path)


    krb5_cmd= (
            "sudo sed -i 's/{}/{}/' {} ; "
            "sudo sed -i '/\\[libdefaults\\]/a \  rdns=false ' {} ;  "
            "sudo echo {} | kinit administrator@{} ;"
            "sudo klist "
            ).format(enterprise_name.upper(), fqdn_domain_name.upper(), krdb_config_path, krdb_config_path, leader_admin_password, fqdn_domain_name.upper())

    realm_cmd= (
        "sudo realm discover {};"
        "echo {}| sudo realm join -U administrator {}  -v;"
        ).format(fqdn_domain_name, leader_admin_password, fqdn_domain_name.upper())

    cmds= set_allow_password + ';' + set_dns_command + ';' + install_packages_cmd + ';' + set_chrony_command + ';' + krb5_cmd + ';' + realm_cmd 


    shell = ShellHandler(ipv4_addr,'ubuntu',None)
    stdout,stderr,exit_status = shell.execute_cmd(cmds, verbose=verbose)

    shell.execute_cmd("sudo reboot now" , verbose=verbose)

    print("  Waiting for reboot (Expect socket closed by peer messages).")
    time.sleep(5)
    status_received = False
    attempts = 0
    stdout2 = None
    while not status_received and attempts < 60:
        attempts += 1
        try:
            admin_user='administrator@' + fqdn_domain_name
            print("  Trying to verify reboot ... creds= {}:{}".format(admin_user,leader_admin_password))
            shell = ShellHandler(ipv4_addr, admin_user, leader_admin_password)
            stdout2,stderr2,exit_status2 = shell.execute_cmd('realm list', verbose=verbose)
            status_received=True
        except paramiko.ssh_exception.SSHException:
            print("  Waiting for reboot (Expect socket closed by peer messages).")
            time.sleep(1)
            pass
        except paramiko.ssh_exception.NoValidConnectionsError:
            print("  Waiting for reboot (Expect socket closed by peer messages).")
            time.sleep(1)
            pass

    try: stdout2
    except:
        errstr = 'Connect after reboot.'
        raise RuntimeError(errstr)


    if stdout2 == None or not 'realm-name: {}'.format(fqdn_domain_name.upper()) in str(stdout2):
        print("join_domain_stdout:" + str(stdout))
        print("join_domain_stderr:" + str(stderr))
        print("verify_domain_stdout:" + str(stdout2))
        print("verify_domain_stderr:" + str(stderr2))
        errstr = 'Cannot detect domain information from ' + name
        if stdout2 == None:
            errstr += ". Could not connect"
        else:
            errstr += ". Missing domain information."
        raise RuntimeError(errstr)
    print("  Reboot Completed by verifying computer is in the domain");

    return {
                "join_domain": {"stdout": stdout, "stderr": stderr, "exit_status": exit_status},
                "verify_join_domain": {"stdout": stdout2, "stderr": stderr2, "exit_status": exit_status2}
            }
