import socket, time, sys, os
import paramiko
import json
from datetime import datetime, timezone

# faker stuff
from faker import Faker

# scheduler stuff.
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

scheduler = BackgroundScheduler()



def emulate_login(login, user_data, built):


    # print(f"At {datetime.now()}, emulating login: " +  json.dumps(login))
    login_from=login['from']
    if not 'ip' in login_from:
        raise RuntimeError("Cannot get from IP for initial connection")

    login_to=login['to']
    if not 'node' in login_to:
        raise RuntimeError("Cannot get from IP for initial connection")


    duration = login['login_length']
    ip_str= login_from['ip']
    mac= login_from['mac']
    to_node_name = login_to['node']
    node = next(filter(lambda node: to_node_name == node['name'], built['deployed']['nodes']))
    #print("To node:" + json.dumps(node,indent=2))
    domain=node['domain']
    targ_ip=node['addresses'][0]['addr']
    #print(f"To node domain, ip = {domain}, {ipv4}")

    # print("user:" + json.dumps(user_data,indent=2))
    user = next(filter(lambda user: login['user'] == user['user_profile']['username'], user_data))
    password=user['user_profile']['password']
    username = user['user_profile']['username']
    #print("Password = " + password)

    mac=fake.mac_address() 
    dev='v'+mac.replace(':','')

    print(f"At {datetime.now()}, connecting from ip {ip_str} with mac {mac}")


    add_command = ( 
            'sudo modprobe dummy ; ' 
            'sudo ip link add ' + dev +' type dummy ; ' 
            'sudo ifconfig ' + dev + ' hw ether ' + mac + ' ; '
            'sudo ip addr add ' + ip_str+'/32' + ' dev ' + dev + ' ; '
            'sudo ip link set dev ' + dev + ' up'
            )

    # print("add-dummy-nic cmd: " + add_command)
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
    fq_username=f"{username}@{domain}"
    print(f"Logging in to {targ_ip} as {fq_username} with password {password}.")
    client.connect(targ_ip,
                   username=fq_username,
                   password=password,
                   sock=sock)

    channel = client.invoke_shell()


    #cmd='bash -i -c "last -10 -i|grep still\\ log"'
    cmd="whoami; python -c 'import time; time.sleep( " + str(duration) + ")' ; echo job completed $RANDOM"
    stdin,stdout,stderr = client.exec_command(cmd, bufsize=4096)

    exit_status = stdout.channel.recv_exit_status()


    #print("Executing cmd on " + targ_ip + ": " + cmd)
    #print("stdout=" + str(stdout.readlines()[0]))

    os.system(del_command)

    channel.close()
    client.close()
    sock.close()
    login_results.append({ "stdout": stdout.readlines(), "stderr": stderr.readlines(), "login": login, "exit_status": exit_status })
    return

def load_json_file(name: str):
    with open(name) as f:
        # Read the file
        ret = json.load(f)
    return ret

def flatten_logins(logins):

    flat_logins = []
    days = logins['days']

    for day in days:
        for user in days[day]:
            flat_logins += days[day][user]
    return flat_logins


def schedule_logins(logins_file, setup_output_file):
    users = logins_file['users']
    flat_logins = flatten_logins(logins_file['logins'])
    executors = {
        'default': ThreadPoolExecutor(2000)
    }
    scheduler = BackgroundScheduler(executors=executors)


    for login in flat_logins:
        job_start = login['login_start']
        job_start = datetime.strptime(job_start, '%Y-%m-%d %H:%M:%S.%f')
        scheduler.add_job( emulate_login, 'date', run_date=job_start, kwargs={'login': login, 'user_data': users, 'built': setup_output_file['enterprise_built']})
        

    return scheduler


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} output.json logins.json")
        sys.exit(1)
    output={}
    output['start_time']=str(datetime.now())
    setup_output_file = load_json_file(sys.argv[1])
    logins_file = load_json_file(sys.argv[2])

    scheduler = schedule_logins(logins_file, setup_output_file)

    scheduler.start()



    while len(scheduler.get_jobs()) > 0:
        wakeup_time = scheduler.get_jobs()[0].next_run_time
        seconds_to_wakeup=(wakeup_time - datetime.now(timezone.utc)).total_seconds()
        print(f"Next job at {wakeup_time}, {seconds_to_wakeup} from now.")
        sleep_time=max(5,seconds_to_wakeup/2)
        time.sleep(sleep_time)

    scheduler.shutdown();

    output['logins']=login_results
    output['end_time']=str(datetime.now())

    with open("logins-output.json", "w") as f:
        json.dump(output,f, default=str)

    return 0


if __name__ == '__main__':
    login_results = []
    fake = Faker()
    #logging.basicConfig()
    #logging.getLogger('apscheduler').setLevel(logging.DEBUG)
    sys.exit(main())


