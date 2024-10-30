from shell_handler import ShellHandler

verbose = True

def setup_moodle_idp (obj):
    control_ipv4_addr=obj['control_addr']
    cloud_config=obj['cloud_config']
    enterprise_url=cloud_config['enterprise_url']
    leader=obj['domain_leader']
    domain_admin_pass=leader['admin_pass']
    user="ubuntu"

    cmd=(
            "sudo systemctl stop jetty apache2;" +
            "sudo sed -i 's/^idp.authn.LDAP.bindDNCredential.*/idp.authn.LDAP.bindDNCredential={}/' /opt/shibboleth-idp/credentials/secrets.properties; " +
            "if [[ -e /etc/ssl/certs/identity.castle.os.crt  ]]; then " +
                "sudo sed -i 's/castle.os/{}/' /opt/shibboleth-idp/conf/idp.properties /opt/shibboleth-idp/conf/attribute-resolver.xml /opt/shibboleth-idp/conf/ldap.properties /etc/apache2/sites-available/identity.castle.os.conf /opt/shibboleth-idp/metadata/idp-metadata.xml /opt/shibboleth-idp/metadata/moodle-md.xml /opt/shibboleth-idp/metadata/sp-metadata.xml ; ".format(enterprise_url) +
                "sudo mv :/var/www/html/identity.castle.os :/var/www/html/identity.{} ; ".format(enterprise_url) +
                "sudo mv /etc/ssl/certs/identity.castle.os.crt /etc/ssl/certs/identity.{}.crt;".format(enterprise_url) +
                "sudo mv /etc/ssl/private/identity.castle.os.key /etc/ssl/private/identity.{}.key;".format(enterprise_url) +
            "fi; " +
            "sudo systemctl start jetty apache2"

            ).format(domain_admin_pass)

    shell = ShellHandler(control_ipv4_addr,user,"")
    stdout,stderr,exit_status = shell.execute_cmd(cmd, verbose=verbose)

    return  {
            "cmd": cmd,
            "stdout": stdout,
            "stderr": stderr,
            }


def setup_moodle_sp(obj):
    control_ipv4_addr=obj['control_addr']
    leader=obj['domain_leader']
    cloud_config=obj['cloud_config']
    enterprise_url=cloud_config['enterprise_url']
    domain_admin_pass=leader['admin_pass']
    user="ubuntu"

    cmd=(
            "sudo systemctl stop apache2;"
            "sudo mysql -u root moodle -e \"update moodle.mdl_config_plugins set value='{}' where name = 'bind_pw' and plugin = 'auth_ldap';\" ;"
            "sudo mysql -u root moodle -e \"SELECT * FROM moodle.mdl_config_plugins where name = 'bind_pw' and plugin = 'auth_ldap';\" ; "
            "if [[ -e /etc/ssl/certs/service.castle.os.crt  ]]; then " +
                "sudo sed -i 's/castle.os/{}/' /etc/shibboleth/metadata/idp-md.xml /etc/shibboleth/shibboleth2.xml /etc/shibboleth/attribute-map.xml /etc/apache2/sites-available/000-service.castle.os.conf ; ".format(enterprise_url) +
                "sudo mv /var/www/html/service.castle.os/ /var/www/html/service.{}; ".format(enterprise_url) +
                "sudo mv /etc/ssl/certs/service.castle.os.crt /etc/ssl/certs/service.{}.crt;".format(enterprise_url) +
                "sudo mv /etc/ssl/private/service.castle.os.key /etc/ssl/private/service.{}.key;".format(enterprise_url) +
            "fi; " +
            "sudo php /var/www/html/service.{}/moodle/admin/cli/purge_caches.php;".format(enterprise_url) + 
            "sudo systemctl start apache2"
            ).format(domain_admin_pass)

    shell = ShellHandler(control_ipv4_addr,user,"")
    stdout,stderr,exit_status = shell.execute_cmd(cmd, verbose=verbose)

    return  {
            "cmd": cmd,
            "stdout": stdout,
            "stderr": stderr,
            }

