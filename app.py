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

      
    data = []
    cmd = "avahi-browse --resolve -t -p _ssh._tcp | grep =;"
    output = subprocess.check_output(cmd, shell=True).decode()
    raw = output.split("\n")
    for i in raw:
        d = []
        spl = i.split(";")
        if len(spl) < 8:
            continue

        name = spl[3] + ".local"
        ipv = spl[2]

        if ipv != "IPv4":
            continue

        d.append("SSH")
        d.append(ipv)
        d.append(name)
        d.append(spl[7]) #ip
        port = spl[8]
        d.append(port)
        data.append(d)
    return render_template("avahi.html", rows=data)

if __name__ == '__main__':
    app.run()
