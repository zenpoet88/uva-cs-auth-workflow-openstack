import math
import random
import string
import password
import sys
import json
from datetime import datetime, timedelta
from joblib import Parallel, delayed

from faker import Faker

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

def generate_new_rsa_key():

    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048
    )

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption()
    )

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    )
    return private_key,public_key



def load_configs(user_roles_filename, enterprise_filename):
    with open(user_roles_filename) as f:
        # Read the file
        user_roles = json.load(f)

    with open(enterprise_filename) as f:
        # Read the file
        enterprise =  json.load(f)
    return user_roles,enterprise

def probabilistic_round(x):
    return int(math.floor(x + random.random()))


def simulate_login(term_no, day_to_work, hour_to_work,user, enterprise, from_node='the internet'):
    start_hour = day_to_work+timedelta(hours=hour_to_work) +timedelta(minutes=random.randint(0,59))
    shared_nodes = list(filter(lambda node: 'shared' in node['roles'], enterprise['nodes']))
    endpoint_nodes = list(filter(lambda node: 'endpoint' in node['roles'], enterprise['nodes']))
    login_profile = user['login_profile']
    home_node = user['home_node']['name']

    login={
            "user": user['user_profile']['username'],
            "session_start": start_hour,
            "session_length": random.randint(1,120)
            }

    to_node = None
    while to_node == None or to_node == from_node:
        if random.random() < float(login_profile['fraction_of_logins_to_personal_machine']):
            # going to home node!
            to_node=home_node
        elif random.random() < float(login_profile['fraction_of_non_personal_logins_to_shared_machines']):
            # going to shared node
            to_node=random.choice(shared_nodes)['name']
        else:
            # not going to personal nor shared node
            to_node=random.choice(endpoint_nodes)['name']

    recursions_no = random.choice(range(int(login_profile['recursive_logins_max'])))
    recursive_logins=[]
    for _ in range(0,recursions_no-1):
        recursive_login = simulate_login(None, day_to_work,hour_to_work,user,enterprise,to_node)
        recursive_logins.append(recursive_login)
        

    login['from']=from_node
    login['to']=to_node
    login['terminal']=term_no
    if len(recursive_logins) > 0:
        login['recursive']=recursive_logins

    # to do, handle recursive logins.
    # if random.random() <  login_fraction
    return login


def simulate_hour(term_no, day_to_work, hour_to_work,logins_this_hour,user, enterprise):
    logins=[]
    for login_no in range(0,logins_this_hour - 1):
        logins.append(simulate_login(term_no, day_to_work, hour_to_work, user, enterprise))
    return logins

def simulate_session(term_no, day_to_simulate,user, enterprise):
    session=[]
    login_profile = user['login_profile']

    day_of_week = day_to_simulate.weekday()
    min_hours_worked=login_profile['activity_daily_min_hours'][day_of_week]
    max_hours_worked=login_profile['activity_daily_max_hours'][day_of_week]
    start_hour_min=login_profile['day_start_hour_min']
    start_hour_max=login_profile['day_start_hour_max']

    logins_per_hour_min=login_profile['activity_min_logins_per_hour']
    logins_per_hour_max=login_profile['activity_max_logins_per_hour']


    hours_worked = random.randint(int(min_hours_worked), int(max_hours_worked))
    start_hour = random.randint(int(start_hour_min),int(start_hour_max))
    parallel_logins = login_profile['terminals_open']

    for hour_no in range(0,hours_worked-1):
        logins_this_hour = probabilistic_round(random.randint(int(logins_per_hour_min),int(logins_per_hour_max))/2.0)
        hour_to_work = start_hour + hour_no
        if hour_to_work > 24:
            break
        logins=simulate_hour(term_no,day_to_simulate, hour_to_work,logins_this_hour,user, enterprise)
        session += logins

    return session

def simulate_user_day(day_to_simulate,user, enterprise):
    sessions=[]
    login_profile = user['login_profile']
    parallel_logins = login_profile['terminals_open']

    for term_no in range(1,int(parallel_logins)):
        session = simulate_session(term_no, day_to_simulate,user, enterprise)
        sessions += session
    
    return sessions

def simulate_day(day_to_simulate,users, enterprise):
        day={}
        for user in users:
            user_day = simulate_user_day(day_to_simulate,user, enterprise)
            username = user['user_profile']['username']
            day[username]= user_day

        return day


def simulate_logins(start_date,days_to_simulate,users, enterprise):
    logins={}
    logins['days']={}

    for i in range(0,days_to_simulate-1):
        day_to_simulate = start_date + timedelta(days=i)
        daystr  = day_to_simulate.strftime('%A, %m/%d/%Y')
        print("Simulating day " + daystr)
        day=simulate_day(day_to_simulate,users, enterprise)
        logins['days'][daystr]=day


    return logins

def create_users(user_roles, enterprise):
    fake = Faker()
    users=[]
    user_nodes = list(filter(lambda node: 'user' in node, enterprise['nodes']))
    print("User nodes are " + str(list(map(lambda node: node['name'], user_nodes) )))

    random.choice(string.ascii_letters)


    # uva compute ids are 3 digits + number + 2-3 digits.

    all_roles = user_roles['roles']

    for user_node in user_nodes:
        user_role_name = user_node['user']
        role = list(filter(lambda role: user_role_name == role['name'], all_roles))
        if len(role) == 0:
            errstr=("Found no role specification for node " + user_node['name'])
            raise RuntimeError(errstr)
        if len(role) >=10:
            errstr=("Found multiple role specification for node " + user_node['name'])
            raise RuntimeError(errstr)
        role = role[0]
        user_nodes = list(filter(lambda node: 'user' in node, enterprise['nodes']))
        user_id = ''.join(
            [random.choice(string.ascii_letters ) for _ in range(3)] +
            [random.choice(string.digits)] +
            [random.choice(string.ascii_letters ) for _ in range(random.choice([2,3]))]
            ).lower()
        private_key,public_key= generate_new_rsa_key()
        user_profile=fake.profile()
        user_profile['password']=password.generate_password(7+int(random.choice(string.digits)))
        user = {
                "user_profile": user_profile,
                "login_profile":  role,
                "ssh_key": { "private_key": private_key, "public_key": public_key },
                "home_node": user_node
                }
        print("Generated user: " + user['user_profile']['username'])
        users.append(user)
    return users


def main():


    start_date=datetime.today()
    days_to_simulate=10


    if len(sys.argv) != 3:
        print("Usage:  python " + sys.argv[0] + " user-roles.json enterprise.json")
        sys.exit(1)

    json_output = {}
    json_output["start_time"] = str(datetime.now())
    json_output["simulation_start"] = str(start_date)
    json_output["simulation_end"] = str(start_date+timedelta(days=days_to_simulate))
    user_roles_filename = sys.argv[1]
    enterprise_filename  = sys.argv[2]
    user_roles,enterprise = load_configs(user_roles_filename, enterprise_filename)
    users=create_users(user_roles,enterprise)
    logins=simulate_logins(start_date, days_to_simulate, users, enterprise)

    json_output['users']=users
    json_output['logins']=logins
    json_output["end_time"] = str(datetime.now())

    with open("logins.json", "w") as f:
        json.dump(json_output,f, default=str)

    return

if __name__ == '__main__':
    # if args are passed, do main line.
        sys.exit(main())


