from dataclasses import dataclass
import json
import os
from typing import Dict, List
from pydantic import BaseModel
from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf, IPVersion
import socket
import aioping
import logging
logger = logging.getLogger(__name__)

class MyServiceInfo(BaseModel):
    ping: str = None
    os: str
    os_version: str
    name: str
    ip: str
    comment: str

PING_UNTIL_REMOVE = 3
@dataclass
class MyServiceRecord:
    ping_left: int = PING_UNTIL_REMOVE
    data: MyServiceInfo = None

class MyListener(ServiceListener):
    default = "None"
    def __init__(self, services):
        super().__init__()
        self.services = services
        self.processors = {}
        self.processors["_spectron._tcp.local."] = self._info_by_type_spectron
        self.processors["_ssh._tcp.local."] = self._info_by_type_ssh

    def _info_by_type_spectron(self, si:ServiceInfo) -> MyServiceRecord:
        msi = MyServiceInfo(
            name = si.server,
            ip = self._get_ip(si.addresses),
            os = si.properties[b'app_name'],
            os_version = si.properties[b'version'],
            comment = "" ,
        )
        return MyServiceRecord(PING_UNTIL_REMOVE,msi)
    
    def _get_ip(self,addresses: List[bytes]) -> str:
        try:
            return socket.inet_ntoa(addresses[0])
        except Exception as ex:
            print(ex)
        return MyListener.default
    
    def _info_by_type_ssh(self, si:ServiceInfo) -> MyServiceRecord:
        msi = MyServiceInfo(
            name = si.server,
            ip = self._get_ip(si.addresses),
            os = MyListener.default,
            os_version = MyListener.default,
            comment = "" ,
        )
        return MyServiceRecord(PING_UNTIL_REMOVE,msi)
    
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        self.services[info.server]  = self.processors[type_](info)
        logger.warning(f"ZeroConf Service {name} updated")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info.server in self.services:
            self.services.pop(info.server)
        logger.warning(f"ZeroConf Service {info.server} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if not info:
            logger.warning(f"no info  for {name}")
            return
        self.services[info.server] = self.processors[type_](info)
        
        logger.warning(f"ZeroConf Service {info.server} added, service info: {info}")

class ServiceRepository:
    def __init__(self):
        self.services: Dict[str,MyServiceRecord] = {}
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self.listener = MyListener(self.services)
        self.browser = ServiceBrowser(self.zeroconf, ["_spectron._tcp.local.","_ssh._tcp.local."], self.listener,delay=1)
        self.comment_fileName = "avahi-comments.json"
        self.comments = {}
        logger.critical("===========Started===========")
        if os.path.exists(self.comment_fileName):
            with open(self.comment_fileName, 'r') as f:
                self.comments = json.load(f)
        
    async def get_services(self) -> List[MyServiceInfo]:
        all: List[MyServiceInfo] = []
        to_remove = []
        for k,i in self.services.items():
            i.data.comment = self.comments[k] if k in self.comments else ""
            try:
                png = await aioping.ping(i.data.ip,timeout=3) * 1000 #"ms"
                i.data.ping = f"{png:.1f} ms"
                all.append(i.data)
                i.ping_left = PING_UNTIL_REMOVE
                logger.info(f"Ping {k} - {i.data.ping}")
            except:
                i.ping_left -= 1
                logger.info(f"No ping for {k}, left {i.ping_left}")
                if i.ping_left <= 0:
                    to_remove.append(k)
                    logger.warning(f"Removed {k}")
        for k in to_remove:
            self.services.pop(k)
        return all
    
    def set_service_comment(self, name, comment):
        self.comments[name] = comment
        with open(self.comment_fileName, 'w') as f:
            json.dump(self.comments, f)
