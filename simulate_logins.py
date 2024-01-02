import socket
import paramiko
import random
import subprocess
import sys
import os
import faker


fake=faker.Faker()

targ_ip = '10.246.115.122'
ip_str= fake.ipv4()

#(
#        str(random.randint(1,254)) + "." + 
#        str(random.randint(1,254)) + "." +
#        str(random.randint(1,254)) + "." + 
#        str(random.randint(1,254))
#    )

dev='dummy'+str(random.randint(0,65536))
mac=fake.mac_address() 

print("Connecting from randomly chosen ip " + ip_str + " with mac " + mac)


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
stdin.close()
stdout.close()


sys.exit(0)
