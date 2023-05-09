from flask import Flask, render_template, request
import subprocess
from time import sleep

app = Flask(__name__)

@app.route('/avahi', methods=['GET', 'POST'])
def avahi():
    if request.method == 'POST':
        id_ = None
        new_name = None
        for key in request.form:
            if key.startswith('new_name.'):
                tmp = request.form[key]
                if tmp:
                    new_name = request.form[key]
                    id_ = key.partition('.')[-1]

        if id_  and new_name:
            print(f"New name: {new_name} row: {id_}")
            cmds = f"\"hostnamectl set-hostname {new_name} && systemctl restart avahi-daemon\""
            host = id_
            subprocess.Popen(f"ssh -oStrictHostKeyChecking=no root@{host} {cmds}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            sleep(5)  

      
    data = []
    cmd = "avahi-browse -a -t | grep SSH"
    output = subprocess.check_output(cmd, shell=True).decode()
    raw = output.split("\n")
    for i in raw:
        d = []
        d.append("SSH")
        spl = i.split(" ")
        if len(spl) < 4:
            continue
        name = spl[3] + ".local"
        ipv = spl[2]
        d.append(ipv)
        d.append(name)
        if ipv == "IPv4":
            resolveCmd = "avahi-resolve-host-name -4 " + name
        else:
            resolveCmd = "avahi-resolve-host-name -6 " + name

        output = subprocess.check_output(resolveCmd, shell=True).decode()
        out2 = output.split("\t")
        if len(out2) > 1:
            d.append(out2[1])
        else:
            d.append("<ERROR>")
        d.append("22")
        data.append(d)
    return render_template("avahi.html", rows=data)

if __name__ == '__main__':
    app.run()
