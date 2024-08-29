from shell_handler import ShellHandler

verbose = True

def setup_moodle_idp (obj):
    control_ipv4_addr=obj['control_addr']
    leader=obj['domain_leader']
    domain_admin_pass=leader['admin_pass']
    user="ubuntu"

    cmd=(
            "sudo systemctl stop jetty;"
            "sudo sed -i 's/^idp.authn.LDAP.bindDNCredential.*/idp.authn.LDAP.bindDNCredential={}/' /opt/shibboleth-idp/credentials/secrets.properties; "
            "sudo systemctl start jetty"
            ).format(domain_admin_pass)

    shell = ShellHandler(control_ipv4_addr,user,"")
    stdout,stderr,exit_status = shell.execute_powershell(cmd, verbose=verbose)

    return  {
            "cmd": cmd,
            "stdout": stdout,
            "stderr": stderr,
            }


def setup_moodle_sp(obj):
    control_ipv4_addr=obj['control_addr']
    leader=obj['domain_leader']
    domain_admin_pass=leader['admin_pass']
    user="ubuntu"

    cmd=(
            "sudo systemctl stop apache2;"
            "sudo mysql -u root moodle -e \"update moodle.mdl_config_plugins set value='{}' where name = 'bind_pw' and plugin = 'auth_ldap';\" ;"
            "sudo mysql -u root moodle -e \"SELECT * FROM moodle.mdl_config_plugins where name = 'bind_pw' and plugin = 'auth_ldap';\" ; "
            "sudo php /var/www/html/service.castle.os/moodle/admin/cli/purge_caches.php;"
            "sudo systemctl start apache2"
            ).format(domain_admin_pass)

    shell = ShellHandler(control_ipv4_addr,user,"")
    stdout,stderr,exit_status = shell.execute_powershell(cmd, verbose=verbose)

    return  {
            "cmd": cmd,
            "stdout": stdout,
            "stderr": stderr,
            }

