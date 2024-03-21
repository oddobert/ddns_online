#!/usr/bin/env python3
"""
 * Build By:
 * https://itheo.tech 2021
 * MIT License
 * Script to set your home (or business) IP address via cloudflare dns on A-record domain record
 * Specially used when you do not have a fixed IP address
"""
import sys
import configparser
import logging
import logging.handlers as handlers
import requests
import threading
from time import sleep
import concurrent.futures
from concurrent.futures import ALL_COMPLETED
import xmlrpc

import CloudFlare


logger = logging.getLogger("ddns")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(processName)s - %(threadName)s - %(levelname)s - %(message)s")

logHandler = handlers.TimedRotatingFileHandler(
    "logs/normal.log", when="M", interval=1, backupCount=0
)
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)

errorLogHandler = handlers.RotatingFileHandler(
    "logs/error.log", maxBytes=5000, backupCount=0
)
errorLogHandler.setLevel(logging.ERROR)
errorLogHandler.setFormatter(formatter)

logger.addHandler(logHandler)
logger.addHandler(errorLogHandler)
# logger.info("A Sample Log Statement")
# logger.error("An error log statement")


class auto_ddns:
    def __init__(self, config_in) -> None:
        self.type = config_in["type"]
        self.zone_id = config_in["zone_id"]
        self.api_token = config_in["api_token"]
        self.ip_address_type = config_in["ip_address_type"]
        self.dns_name = config_in["dns_name"]

        logger.info(
            f" {self.zone_id} {self.api_token } {self.ip_address_type} {self.dns_name} "
        )
        self.current_ip = None
        self.external_ip = None
        self.cf = None
        self.new_dns_record = None
        self.dns_id = None

    def main(self):
        self.current_ip = self.get_ip()

        if not self.current_ip:
            return False
        if self.type.lower() == "cloudflare":
            if not self.connect_cloud_dns():
                return False

            if not self.get_cloud_dns():
                return False

            if self.external_ip is not None and self.external_ip == self.current_ip:
                return True

            if not self.set_cloud_dns():
                return False
        if self.type.lower() == "gandi":
            if not self.connect_gandi_dns():
                return False

            if not self.get_gandi_dns():
                return False

            if self.external_ip is not None and self.external_ip == self.current_ip:
                return True

            if not self.set_cloud_dns():
                return False

        return True



    @staticmethod
    def get_ip():
        try:
            result = requests.get("https://checkip.amazonaws.com")
            if result.status_code == 200:
                logging.info(f"got ip {result.text.strip()}")
                return result.text.strip()
            else:
                print("No access to outside world")
                return False
        except Exception as e:
            logger.error(e)
            return False

    def connect_gandi_dns(self):
        api = xmlrpc.ServerProxy('https://rpc.gandi.net/xmlrpc/')
        apikey=self.api_token
        r = api.catalog.list(apikey, {'product': {'type': 'domain', 'description': '.at'}})
        print(r)
        pass

    def get_gandi_dns(self):
        #get the dns
        set_gandi_dns()

    def set_gandi_dns(self):
        pass

    def connect_cloud_dns(self):
        try:
            self.cf = CloudFlare.CloudFlare(token=self.api_token)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            print("connection to cloudlfare failed")
            logger.error("API connection failed: {e}")
            return False

        return True

    def get_cloud_dns(self):
        print(self.dns_name)
        try:
            params = {
                "name": self.dns_name,
                "match": "all",
                "type": self.ip_address_type,
            }
            logger.info(f'params {params}, {self.zone_id}, {self.dns_name}')
            dns_records = self.cf.zones.dns_records.get(self.zone_id, params=params)

        except CloudFlare.exceptions.CloudFlareAPIError as e:
            logger.error(
                "/zones/dns_records/export %s - %d %s - api call failed"
                % (self.zone_id, e, e)
            )
            return False
        logger.info(f"dns_records {self.dns_name} {dns_records}")
        for dns_record in dns_records:
            try:
                self.external_ip = dns_record["content"]

                if self.current_ip != self.external_ip:
                    self.dns_id = dns_record["id"] #why

                    self.new_dns_record = {
                        "name": self.dns_name,
                        "type": self.ip_address_type,
                        "content": self.current_ip,
                        "proxied": dns_record["proxied"],
                    }
                else:
                    logger.info("Getter unchanged")
                    return False
            except Exception as e:
                logger.error(e)
                return False
        logger.info("GETTER RAN OK")
        return True

    def set_cloud_dns(self):
        logging.info(f"Setting cloud")
        try:
            logger.info(f"self.new_dns_record {self.new_dns_record}")
            dns_record = self.cf.zones.dns_records.put(
                self.zone_id, self.dns_id, data=self.new_dns_record
            )  # ,
            print(dns_record)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            logger.error(
                "/zones.dns_records.post %s - %d %s - api call failed"
                % (self.dns_name, e, e)
            )
            return False

        logger.info(
            "UPDATED: %s %s -> %s"
            % (self.dns_name, self.external_ip, self.current_ip)
        )
        return True


def run_one_ddns(config):
    print(config['dns_name'])
    #logging(f'starting {config[dns_name]}')

    ddns = auto_ddns(config)

    while True:
        if ddns.main():
            sleep(300)  # 15 minutes
        else:
            # I guess something went wrong, let's give the script a bit more time.
            sleep(600)  # 30 minutes


if __name__ == "__main__":
    configs = configparser.ConfigParser()
    configs.read("config.ini")
    config_parser = [dict(configs.items(s)) for s in configs.sections()]
    logging.info(config_parser)
    with concurrent.futures.ThreadPoolExecutor(len(config_parser)) as executor:
        fs = executor.map(run_one_ddns, config_parser)
        # x = threading.Thread(target=run_one_ddns,args=(configs[configs.sections()],range(len(configs.sections()))))
    concurrent.futures.wait(fs=fs, timeout=None, return_when=ALL_COMPLETED)
    print('Done')


