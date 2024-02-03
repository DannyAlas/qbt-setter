import json
import logging
import os
import time

import requests

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s : %(message)s",
)

log = logging.getLogger(__name__)
qbt_url = "http://10.32.32.20:8080"


def main():
    print(
        r"""
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
This script will keep changing it back to eth0
"""
    )
    interval = 20
    while True:
        try:
            login_payload = {
                "username": os.environ["QBT_USERNAME"],
                "password": os.environ["QBT_PASS"],
            }
            login_headers = {"Referer": qbt_url}
            login_response = requests.post(
                qbt_url + "/api/v2/auth/login",
                data=login_payload,
                headers=login_headers,
            )
            cookie = "SID=" + str(login_response.cookies.get_dict()["SID"])

            settings = requests.get(
                qbt_url + "/api/v2/app/preferences", headers={"Cookie": cookie}
            )
            settings_json = settings.json()
            if settings_json.get("current_network_interface") != "eth0":
                json_data = {"current_network_interface": "eth0"}
                requests.put(
                    qbt_url + "/api/v2/app/preferences",
                    json=json.dumps(json_data),
                    headers={"Cookie": cookie},
                )
                log.info("Changed network interface to eth0")
                interval = 240
            else:
                log.info("Network interface is already set to eth0")
                interval = 240
            time.sleep(interval)
        except Exception as e:
            log.error(f"Error: {e}")
            interval = 20
            time.sleep(interval)


if __name__ == "__main__":
    main()
