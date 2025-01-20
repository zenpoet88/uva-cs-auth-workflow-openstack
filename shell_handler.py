import paramiko
import sys
import socket


class ShellHandler:

    def __init__(self, host, user, password, from_ip: str = None, verbose=False):

        self.verbose = verbose
        self.sock = None
        if from_ip is not None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((from_ip, 0))           # set source address
            self.sock.connect((host, 22))       # connect to the destination address

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=user, password=password, port=22, sock=self.sock)
        self.sftp = self.ssh.open_sftp()

    def __del__(self):

        if hasattr(self, "ssh"):
            self.ssh.close()
            self.ssh = None

        if self.sock is not None:
            self.sock.close()

    def execute_cmd(self, cmd, verbose=False):
        """

        :param cmd: the command to be executed on the remote computer
        :examples:  execute('ls')
                    execute('finger')
                    execute('cd folder_name')
        """

        if verbose or self.verbose:
            print("Final cmd to execute:" + cmd)
        stdin, stdout, stderr = self.ssh.exec_command(cmd, bufsize=0, get_pty=True)
        stdout_lines = []
        stderr_lines = []
        while not stdout.channel.exit_status_ready():

            # Stream stdout
            if stdout.channel.recv_ready():
                for line in iter(lambda: stdout.readline(), ""):
                    stdout_lines.append(line)
                    if verbose or self.verbose:
                        print(line, end='')  # Print each line as it arrives

            # Stream stderr -- is this correct?
            if stderr.channel.recv_ready():
                for err_line in iter(lambda: stderr.readline(), ""):
                    stderr_lines.append(err_line)
                    if verbose or self.verbose:
                        print(err_line, end='')

        exit_status = stdout.channel.recv_exit_status()
        return stdout_lines, stderr_lines, exit_status

    def execute_powershell(self, cmd, verbose=False, exit=False):
        quoted_cmd = cmd.replace('\\"', '\\"').replace("\\'", "\\").replace('"', '\\"')
        new_cmd = 'powershell -c "' + quoted_cmd + '"'
        if verbose or self.verbose:
            print("Unquoted command for powershell:" + cmd)
        if exit:
            sys.exit(1)
        return self.execute_cmd(new_cmd, verbose=verbose)

    def put_file(self, src_filename: str, dst_filename: str, verbose: bool = False):
        self.sftp.put(src_filename, dst_filename)
        return
