from dotenv import load_dotenv
from os import getenv

load_dotenv()

hosts = [
    (
        "192.168.31.134",
        {
            "ssh_user": getenv('RASPBERRY_SSH_USER'),
            "ssh_password": getenv('RASPBERRY_SSH_PASSWORD'),
            "ssh_look_for_keys": False,
            "ssh_allow_agent": False,
        }
    )
]
