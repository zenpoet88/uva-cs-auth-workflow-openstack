import paramiko
import sys


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

    def execute_cmd(self, cmd, verbose=False):
        """

        :param cmd: the command to be executed on the remote computer
        :examples:  execute('ls')
                    execute('finger')
                    execute('cd folder_name')
        """

        if verbose:
            print("Final cmd to execute:" + cmd)
        stdin,stdout,stderr = self.ssh.exec_command(cmd, bufsize=4096)
        stdout_lines = [] 
        stderr_lines = [] 
        while not stdout.channel.exit_status_ready():
            stdout_newlines=stdout.readlines()
            stdout_lines.append(stdout_newlines)
            stderr_newlines=stderr.readlines()
            stderr_lines.append(stderr_newlines)
            if verbose:
                for line in stdout_newlines:
                    print(line)
                for line in stderr_newlines:
                    print(line)
        

        exit_status = stdout.channel.recv_exit_status()
        stdout_newlines=stdout.readlines()
        stdout_lines.append(stdout_newlines)
        stderr_newlines=stderr.readlines()
        stderr_lines.append(stderr_newlines)
        if verbose:
            for line in stdout_newlines:
                print(line)
            for line in stderr_newlines:
                print(line)
        return stdout_lines, stderr_lines, exit_status 

    def execute_powershell(self, cmd, verbose=False, exit=False):
        quoted_cmd = cmd.replace('\\"', '\\"').replace("\\'", "\\").replace('"', '\\"')
        new_cmd = 'powershell -c "' + quoted_cmd + '"'
        if verbose:
            print("Unquoted command for powershell:" + cmd)
        if exit:
            sys.exit(1)
        return self.execute_cmd(new_cmd, verbose=verbose)

