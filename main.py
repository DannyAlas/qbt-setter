import json
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

import requests
from requests import Response, Session

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s : %(message)s",
)

log = logging.getLogger(__name__)


class QBittorrentClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url: str = base_url.rstrip('/')
        self.username: str = username
        self.password: str = password
        self.session: Session = requests.Session()
        self.session.headers.update({'Referer': self.base_url})
        self.is_authenticated: bool = False

    def authenticate(self) -> None:
        login_payload: Dict[str, str] = {"username": self.username, "password": self.password}
        try:
            response: Response = self.session.post(
                f"{self.base_url}/api/v2/auth/login", data=login_payload
            )
            response.raise_for_status()
            if response.text != 'Ok.':
                raise ValueError(f"Login failed: {response.text}")
            self.is_authenticated = True
            log.info("Authenticated successfully.")
        except requests.RequestException as e:
            log.error(f"Authentication failed due to a network error: {e}")
            self.is_authenticated = False
            raise
        except Exception as e:
            log.error(f"Authentication failed: {e}")
            self.is_authenticated = False
            raise

    def get_preferences(self) -> Dict[str, Any]:
        if not self.is_authenticated:
            self.authenticate()
        try:
            response: Response = self.session.get(f"{self.base_url}/api/v2/app/preferences")
            response.raise_for_status()
            preferences: Dict[str, Any] = response.json()
            return preferences
        except requests.RequestException as e:
            log.error(f"Failed to get preferences due to a network error: {e}")
            self.is_authenticated = False
            raise
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse preferences JSON: {e}")
            self.is_authenticated = False
            raise
        except Exception as e:
            log.error(f"Failed to get preferences: {e}")
            self.is_authenticated = False
            raise

    def set_preferences(self, preferences: Dict[str, Any]) -> None:
        if not self.is_authenticated:
            self.authenticate()
        try:
            data: Dict[str, str] = {'json': json.dumps(preferences)}
            response: Response = self.session.post(
                f"{self.base_url}/api/v2/app/setPreferences", data=data
            )
            response.raise_for_status()
            log.info("Preferences updated successfully.")
        except requests.RequestException as e:
            log.error(f"Failed to set preferences due to a network error: {e}")
            self.is_authenticated = False
            raise
        except Exception as e:
            log.error(f"Failed to set preferences: {e}")
            self.is_authenticated = False
            raise


def main() -> None:
    print(r"""
      $$$$$$$$\ $$\       $$\                 $$\                             $$\                         $$\       $$\ 
      \__$$  __|$$ |      \__|                \__|                            $$ |                        \__|      $$ |
         $$ |   $$$$$$$\  $$\  $$$$$$$\       $$\  $$$$$$$\        $$$$$$$\ $$$$$$\   $$\   $$\  $$$$$$\  $$\  $$$$$$$ |
         $$ |   $$  __$$\ $$ |$$  _____|      $$ |$$  _____|      $$  _____|\_$$  _|  $$ |  $$ |$$  __$$\ $$ |$$  __$$ |
         $$ |   $$ |  $$ |$$ |\$$$$$$\        $$ |\$$$$$$\        \$$$$$$\    $$ |    $$ |  $$ |$$ /  $$ |$$ |$$ /  $$ |
         $$ |   $$ |  $$ |$$ | \____$$\       $$ | \____$$\        \____$$\   $$ |$$\ $$ |  $$ |$$ |  $$ |$$ |$$ |  $$ |
         $$ |   $$ |  $$ |$$ |$$$$$$$  |      $$ |$$$$$$$  |      $$$$$$$  |  \$$$$  |\$$$$$$  |$$$$$$$  |$$ |\$$$$$$$ |
         \__|   \__|  \__|\__|\_______/       \__|\_______/       \_______/    \____/  \______/ $$  ____/ \__| \_______|
                                                                                                $$ |
                                                                                                $$ |
                                                                                                \__|
      But qbt keeps changing the network interface on start up, or just randomly regardless of the settings.
      This script will keep changing it back to eth0.
      """)
    qbt_url: str = os.getenv("QBT_URL", "http://localhost:8080")
    qbt_username: Optional[str] = os.getenv("QBT_USERNAME")
    qbt_password: Optional[str] = os.getenv("QBT_PASS")
    desired_interface: str = os.getenv("DESIRED_NETWORK_INTERFACE", "eth0")

    if not qbt_username or not qbt_password:
        missing_env_vars = []
        if not qbt_username:
            missing_env_vars.append("QBT_USERNAME")
        if not qbt_password:
            missing_env_vars.append("QBT_PASS")
        log.error(f"Missing environment variables: {', '.join(missing_env_vars)}")
        sys.exit(1)

    client = QBittorrentClient(qbt_url, qbt_username, qbt_password)
    interval: int = 20

    while True:
        try:
            preferences: Dict[str, Any] = client.get_preferences()
            current_interface: str = preferences.get("current_network_interface", "")
            if current_interface != desired_interface:
                client.set_preferences({"current_network_interface": desired_interface})
                log.info(f"Changed network interface to {desired_interface}.")
                interval = 240
            else:
                log.info(f"Network interface is already set to {desired_interface}.")
                interval = 240
        except Exception as e:
            log.error(f"An error occurred: {e}")
            interval = 20
            client.is_authenticated = False  # Force re-authentication on next loop
        time.sleep(interval)


if __name__ == "__main__":
    main()
