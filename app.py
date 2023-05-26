
from flask import Flask, render_template, request
import subprocess
from time import sleep

app = Flask(__name__)

@app.route('/avahi', methods=['GET', 'POST'])
def avahi():
    if request.method == 'POST':
        host = None
        new_name = None
        for key in request.form:
            if key.startswith('new_name.'):
                new_name = request.form[key]
                print(f"Before New name: {key} host: {new_name}")
                if new_name:
                    host = key.partition('.')[-1]
                    break

        if host  and new_name:
            print(f"New name: {new_name} host: {host}")
            cmds = f"\"hostnamectl set-hostname {new_name} && systemctl restart avahi-daemon\""
            subprocess.Popen(f"ssh -oStrictHostKeyChecking=no root@{host} {cmds}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            sleep(5)

    ssh_services = discover_ssh_services()
    spectron_services = discover_spectron_services()

    merged_services = []
    for ssh in ssh_services:
        ip_ssh = ssh[3]
        for spec in spectron_services:
            ip = spec[3]
            if ip_ssh == ip:
                ssh[0] = spec[0]
                ssh[1] = spec[1]
        merged_services.append(ssh)
        
    return render_template("avahi.html", rows = merged_services)

if __name__ == '__main__':
    app.run()
    
#функция содержащая в себе данные о ssh сервисе
def discover_ssh_services():
    data = []
    cmd = "avahi-browse --resolve -t -p _ssh._tcp | grep ="
    try:
        output = subprocess.check_output(cmd, shell=True).decode()
        raw = output.split("\n")
        for i in raw:
            d = []
            spl = i.split(";")
            if len(spl) < 10:
                continue

           
            ip = spl[7]
            name = spl[3] + ".local"
            ipv = spl[2]

            if ipv != "IPv4":
                continue
            
            d.append('<unknown>') 
            d.append('<unknown>') 
            d.append(name)
            d.append(ip)
            data.append(d)
    except:
        pass
  
    return data

#функция содержащая в себе данные о spectron сервисе (добавлена)
def discover_spectron_services():
    data = []
    cmd = "avahi-browse --resolve -t -p _spectron._tcp | grep ="
    try:
        output = subprocess.check_output(cmd, shell=True).decode()
        raw = output.split("\n")
        for i in raw:
            d = []
            spl = i.split(";")
            if len(spl) < 10:
                continue
            
            version, os = spl[9].split()
            version_f = version.replace('"', ' ').strip().split('=')[1]
            os_f = os.replace('"', ' ').strip().split('=')[1]
            ip = spl[7]
            name = spl[3] + ".local"            
            ipv = spl[2]

            if ipv != "IPv4":
                continue
      
            d.append(version_f)
            d.append(os_f)
            d.append(name)
            d.append(ip)
            data.append(d)
    except:
        pass
    
    return data

