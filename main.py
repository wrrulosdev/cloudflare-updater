import logging
import os
import time
import sys
from typing import Optional, Any
import requests
from dotenv import load_dotenv

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('cloudflare_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


def parse_bool(value: Optional[str], default: bool = True) -> bool:
    """
    Parse a string from environment to a boolean.
    Accepts: '1', 'true', 'yes', 'y', 'on' (case-insensitive) as True.
    Anything else (including None) falls back to default.
    """
    if value is None:
        return default
    
    return value.strip().lower() in ('1', 'true', 'yes', 'y', 'on')


class CloudflareUpdater:
    def __init__(
        self,
        api_token: str,
        zone_id: str,
        record_name: str,
        proxied: bool = True,
        api_url: str = 'https://api.cloudflare.com/client/v4'
    ) -> None:
        self.api_token: str = api_token
        self.zone_id: str = zone_id
        self.record_name: str = record_name
        self.proxied: bool = proxied
        self.api_url: str = api_url

    def get_dns_record_id(self) -> Optional[str]:
        """
        Retrieves the DNS record ID for the specified record name.
        :return: The DNS record ID as a string, or None if not found.
        """
        url: str = f"{self.api_url}/zones/{self.zone_id}/dns_records"
        headers: dict[str, str] = {
            'Authorization': f"Bearer {self.api_token}",
            'Content-Type': 'application/json'
        }
        params: dict[str, str] = {
            'type': 'A',
            'name': self.record_name
        }

        try:
            response: requests.Response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            records: list[dict[str, Any]] = response.json().get('result', [])

            if not records:
                logging.error(f'DNS record not found for {self.record_name}')
                return None

            return records[0]['id']
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching DNS record ID: {e}")
            return None

    def update_dns_record(self, new_ip: str) -> None:
        """
        Updates the DNS record with the new IP address.
        :param new_ip: The new public IP address.
        """
        record_id: Optional[str] = self.get_dns_record_id()

        if not record_id:
            logging.error(f"Unable to update DNS record: Record ID not found for {self.record_name}")
            return

        url: str = f"{self.api_url}/zones/{self.zone_id}/dns_records/{record_id}"
        headers: dict[str, str] = {
            'Authorization': f"Bearer {self.api_token}",
            'Content-Type': 'application/json'
        }
        data: dict[str, Any] = {
            'type': 'A',
            'name': self.record_name,
            'content': new_ip,
            'ttl': 120,
            'proxied': self.proxied
        }

        try:
            response: requests.Response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            logging.info(
                f"DNS record updated successfully: {self.record_name} -> {new_ip} (proxied={self.proxied})"
            )
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error updating DNS record: {e}")

    @staticmethod
    def get_public_ip() -> Optional[str]:
        """
        Fetches the public IP address using an external service.
        :return: The public IP address as a string, or None if an error occurs.
        """
        try:
            response: requests.Response = requests.get('https://api.ipify.org?format=json')
            response.raise_for_status()
            ip_data: dict[str, Any] = response.json()
            return ip_data.get('ip')
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching public IP: {e}")
            return None


def load_multiple_records() -> list[dict[str, Any]]:
    """
    Loads multiple Cloudflare record configurations from environment variables.
    You can define multiple records like:
      API_TOKEN_1, ZONE_ID_1, RECORD_NAME_1, PROXIED_1
      API_TOKEN_2, ZONE_ID_2, RECORD_NAME_2, PROXIED_2
      etc.
    :return: A list of record configuration dictionaries.
    """
    records: list[dict[str, Any]] = []
    index: int = 1

    while True:
        api_token: Optional[str] = os.getenv(f'API_TOKEN_{index}')
        zone_id: Optional[str] = os.getenv(f'ZONE_ID_{index}')
        record_name: Optional[str] = os.getenv(f'RECORD_NAME_{index}')
        proxied_env: Optional[str] = os.getenv(f'PROXIED_{index}')

        # Stop when no more numbered records are found
        if not api_token or not zone_id or not record_name:
            break

        proxied: bool = parse_bool(proxied_env, default=True)
        records.append({
            'api_token': api_token,
            'zone_id': zone_id,
            'record_name': record_name,
            'proxied': proxied
        })
        index += 1

    return records


def loop() -> None:
    """ Infinite loop to update IP to Cloudflare in case router IP changes """

    # Load multiple record configurations (if exists)
    records: list[dict[str, Any]] = load_multiple_records()

    # Fallback to single record if no numbered ones are defined
    if not records:
        api_token: Optional[str] = os.getenv('API_TOKEN')
        zone_id: Optional[str] = os.getenv('ZONE_ID')
        record_name: Optional[str] = os.getenv('RECORD_NAME')
        proxied_env: Optional[str] = os.getenv('PROXIED')

        if api_token and zone_id and record_name:
            proxied: bool = parse_bool(proxied_env, default=True)
            records.append({
                'api_token': api_token,
                'zone_id': zone_id,
                'record_name': record_name,
                'proxied': proxied
            })
        else:
            missing: list[str] = []

            if api_token is None:
                missing.append('API_TOKEN')

            if zone_id is None:
                missing.append('ZONE_ID')

            if record_name is None:
                missing.append('RECORD_NAME')

            logging.error(f'Missing required environment variables: {", ".join(missing)}')
            sys.exit(1)

    delay: int = 120
    current_ipaddress: Optional[str] = CloudflareUpdater.get_public_ip()

    if current_ipaddress is None:
        logging.error('Could not get the current IP address at first. Do you have an Internet connection?')
        sys.exit(1)

    updaters: list[CloudflareUpdater] = [
        CloudflareUpdater(
            api_token=record['api_token'],
            zone_id=record['zone_id'],
            record_name=record['record_name'],
            proxied=record.get('proxied', True)
        )
        for record in records
    ]
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

        for updater in updaters:
            updater.update_dns_record(new_ipaddress)

        current_ipaddress = new_ipaddress
        first = False


if __name__ == '__main__':
    loop()
