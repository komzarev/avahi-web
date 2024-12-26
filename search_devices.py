import subprocess
from time import sleep
import json
import os

fileName = "avahi-comments.json"
comments = {}

def get_services():
    global comments
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
    for s in merged_services:
        if s[2] not in comments:
            comments[s[2]] = ""

    merged_services.sort(key=lambda x : x[0])
    return merged_services

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