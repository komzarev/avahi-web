import json
import os
from typing import Dict, List
from pydantic import BaseModel
from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf, IPVersion
import socket
from ping3 import ping

class MyServiceInfo(BaseModel):
    ping: str = None
    os: str
    os_version: str
    name: str
    ip: str
    comment: str

class MyListener(ServiceListener):
    default = "None"
    def __init__(self, services):
        super().__init__()
        self.services = services
        self.processors = {}
        self.processors["_spectron._tcp.local."] = self._info_by_type_spectron
        self.processors["_ssh._tcp.local."] = self._info_by_type_ssh

    def _info_by_type_spectron(self, si:ServiceInfo) -> MyServiceInfo:
        msi = MyServiceInfo(
            name = si.server,
            ip = self._get_ip(si.addresses),
            os = si.properties[b'app_name'],
            os_version = si.properties[b'version'],
            comment = "" ,
        )
        return msi
    
    def _get_ip(self,addresses: List[bytes]) -> str:
        try:
            return socket.inet_ntoa(addresses[0])
        except Exception as ex:
            print(ex)
        return MyListener.default
    
    def _info_by_type_ssh(self, si:ServiceInfo) -> MyServiceInfo:
        msi = MyServiceInfo(
            name = si.server,
            ip = self._get_ip(si.addresses),
            os = MyListener.default,
            os_version = MyListener.default,
            comment = "" ,
        )
        return msi
    
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        self.services[info.server]  = self.processors[type_](info)
        print(f"Service {name} updated")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        self.services.pop(info.server)
        print(f"Service {info.server} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if not info:
            print(f"not info {name}")
            return
        self.services[info.server] = self.processors[type_](info)
        
        print(f"Service {info.server} added, service info: {info}")

class ServiceRepository:
    def __init__(self):
        self.services: Dict[str,MyServiceInfo] = {}
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self.listener = MyListener(self.services)
        self.browser = ServiceBrowser(self.zeroconf, ["_spectron._tcp.local.","_ssh._tcp.local."], self.listener,delay=1)
        self.comment_fileName = "avahi-comments.json"
        self.comments = {}
        if os.path.exists(self.comment_fileName):
            with open(self.comment_fileName, 'r') as f:
                self.comments = json.load(f)
        
    def get_services(self) -> List[MyServiceInfo]:
        all: List[MyServiceInfo] = []
        for k,i in self.services.items():
            i.comment = self.comments[k] if k in self.comments else ""
            png = ping(i.ip,unit="ms")
            if png:
                i.ping = f"{png:.1f} ms"
                all.append(i)
        return all
    
    def set_service_comment(self, name, comment):
        self.comments[name] = comment
        with open(self.comment_fileName, 'w') as f:
            json.dump(self.comments, f)