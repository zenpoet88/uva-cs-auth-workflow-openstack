import paramiko
import re


class ShellHandler:

    def __init__(self, host, user, psw):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=user, password=psw, port=22)

        channel = self.ssh.invoke_shell()
        self.stdin = channel.makefile('wb')
        self.stdout = channel.makefile('r')

    def __del__(self):
        self.ssh.close()

    def execute_cmd(self, cmd):
        """

        :param cmd: the command to be executed on the remote computer
        :examples:  execute('ls')
                    execute('finger')
                    execute('cd folder_name')
        """

        stdin,stdout,stderr = self.ssh.exec_command(cmd, bufsize=4096)
        exit_status = stdout.channel.recv_exit_status()
        lines = stdout.readlines()
        return lines, stderr.readlines(), exit_status 

    def execute_powershell(self, cmd):
        quoted_cmd = cmd.replace("\\", "\\\\").replace('"', '\\"')
        new_cmd = 'powershell -c "' + quoted_cmd + '"'
        print("Quoted powershell command:" + new_cmd)
        return self.execute_cmd(new_cmd)

