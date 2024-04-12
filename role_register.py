from shell_handler import ShellHandler
import paramiko

def register_windows_instance(obj):
    control_ipv4_addr=obj['control_addr']
    password=obj['password']
    user='Administrator'
    cmd = 'slmgr.vbs /skms uvakms.eservices.virginia.edu; Start-Sleep -s 15; slmgr.vbs /ato; start-sleep -s 45; Get-CimInstance SoftwareLicensingProduct -Filter "Name like \'Windows%\'" | where { $_.PartialProductKey } | select Description, LicenseStatus'
    try:
        shell = ShellHandler(control_ipv4_addr,user,password)
        stdout,stderr,exit_status = shell.execute_powershell(cmd)
    except paramiko.ssh_exception.AuthenticationException:
        print("Could not connect with credentials to windows, already registered?")
        return {}

    return {"node_details": obj, "stdout": stdout, "stderr": stderr, "exit_status": exit_status}

