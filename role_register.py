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

