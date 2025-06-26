import logging
import os
import time
import sys
from typing import Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('cloudflare_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


class CloudflareUpdater:
    def __init__(self, api_token: str, zone_id: str, record_name: str, api_url: str = 'https://api.cloudflare.com/client/v4') -> None:
        self.api_token: str = api_token
        self.zone_id: str = zone_id
        self.record_name: str = record_name
        self.api_url: str = api_url

    def get_dns_record_id(self) -> Optional[str]:
        """
        Retrieves the DNS record ID for the specified record name.
        :return: The DNS record ID as a string, or None if not found.
        """
        url: str = f"{self.api_url}/zones/{self.zone_id}/dns_records"
        headers: dict = {
            'Authorization': f"Bearer {self.api_token}",
            'Content-Type': 'application/json'
        }
        params: dict = {
            'type': 'A',
            'name': self.record_name
        }

        try:
            response: requests.Response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            records: list = response.json().get('result', [])

            if records:
                return records[0]['id']
            else:
                logging.error('DNS record not found for %s', self.record_name)
                return None
        except requests.exceptions.RequestException as e:
            logging.error('Error fetching DNS record ID: %s', e)
            return None

    def update_dns_record(self, new_ip: str) -> None:
        """
        Updates the DNS record with the new IP address.
        :param new_ip: The new public IP address.
        """
        record_id: Optional[str] = self.get_dns_record_id()
        if not record_id:
            logging.error('Unable to update DNS record: Record ID not found')
            return

        url: str = f"{self.api_url}/zones/{self.zone_id}/dns_records/{record_id}"
        headers: dict = {
            'Authorization': f"Bearer {self.api_token}",
            'Content-Type': 'application/json'
        }
        data: dict = {
            'type': 'A',
            'name': self.record_name,
            'content': new_ip,
            'ttl': 120,
            'proxied': True
        }

        try:
            response: requests.Response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            logging.info('DNS record updated successfully: %s -> %s', self.record_name, new_ip)

        except requests.exceptions.RequestException as e:
            logging.error('Error updating DNS record: %s', e)

    @staticmethod
    def get_public_ip() -> Optional[str]:
        """
        Fetches the public IP address using an external service.
        :return: The public IP address as a string, or None if an error occurs.
        """
        try:
            response: requests.Response = requests.get('https://api.ipify.org?format=json')
            response.raise_for_status()
            ip_data: dict = response.json()
            return ip_data.get('ip')
        except requests.exceptions.RequestException as e:
            logging.error('Error fetching public IP: %s', e)
            return None

def loop() -> None:
    """ Infinite loop to update IP to Cloudflare in case router IP changes """
    api_token: str = os.getenv('API_TOKEN')
    zone_id: str = os.getenv('ZONE_ID')
    record_name: str = os.getenv('RECORD_NAME')

    if api_token is None or zone_id is None or record_name is None:
        missing: list[str] = []

        if api_token is None:
            missing.append('API_TOKEN')

        if zone_id is None:
            missing.append('ZONE_ID')

        if record_name is None:
            missing.append('RECORD_NAME')

        logging.error(f'Missing required environment variables: {", ".join(missing)}')

    delay: int = 120
    current_ipaddress: Optional[str] = CloudflareUpdater.get_public_ip()

    if current_ipaddress is None:
        logging.error('Could not get the current IP address at first. Do you have an Internet connection?')
        sys.exit(1)

    updater: CloudflareUpdater = CloudflareUpdater(api_token, zone_id, record_name)
    first: bool = True

    while True:
        if not first:
            time.sleep(delay)

        new_ipaddress: Optional[str] = CloudflareUpdater.get_public_ip()

        if new_ipaddress is None:
            logging.warning('Could not get the new IP address. Skipping...')
            continue

        if new_ipaddress == current_ipaddress and not first:
            logging.info('The current IP address is the same as the previous one. Skipping...')
            continue

        updater.update_dns_record(new_ipaddress)
        current_ipaddress = new_ipaddress
        first = False


if __name__ == '__main__':
    loop()
