import socket
import paramiko
import sys
import os
from datetime import datetime, timedelta
from faker import Faker


def simulate_login(to_ip, user):

    targ_ip = '10.246.115.122'
    ip_str= fake.ipv4()

    mac=fake.mac_address() 
    dev='dummy'+mac.replace(':','')

    print("Connecting from chosen ip " + ip_str + " with mac " + mac)


    add_command = ( 
            'sudo modprobe dummy ; ' 
            'sudo ip link add ' + dev +' type dummy ; ' 
            'sudo ifconfig ' + dev + ' hw ether ' + mac + ' ; '
            'sudo ip addr add ' + ip_str+'/32' + ' dev ' + dev + ' ; '
            'sudo ip link set dev ' + dev + ' up'
            )


    os.system(add_command)

    #        'sudo ip addr del ' + ip_str+'/32' + ' dev ' + dev + ' ; ' 
    del_command = (
            'sudo ip link delete ' + dev + ' type dummy'
            )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.bind((ip_str, 0))           # set source address
    sock.connect((targ_ip, 22))       # connect to the destination address

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(targ_ip,
                   username='ubuntu',
                   sock=sock)

    channel = client.invoke_shell()


    cmd='bash -i -c "last -10 -i|grep still\\ log"'
    stdin,stdout,stderr = client.exec_command(cmd, bufsize=4096)

    print("Executing cmd on " + targ_ip + ": " + cmd)
    print("stdout=" + str(stdout.readlines()[0]))

    os.system(del_command)

    channel.close()
    client.close()
    sock.close()

def load_json_file(name: str):
    with open(name) as f:
        # Read the file
        ret = json.load(f)
    return ret


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} enterprise.json logins.json")
        sys.exit(1)
    output={}
    output['start_date']=datetime.today()
    enterprise = load_config_file(sys.argv[1])
    logins = load_config_file(sys.argv[2])
    users = logins['users']
    users = logins['logins']

    output['start_date']=datetime.today()


    # empty
    sys.exit(0)


if __name__ == '__main__':
    fake = Faker()
    sys.exit(main())


