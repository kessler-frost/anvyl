import subprocess
from typing import Optional

def install_beszel(host_ip: str, public_key: Optional[str] = None) -> str:
    cmd = ["ssh", f"root@{host_ip}", "curl -sSL https://get.beszel.io | sh"]
    if public_key:
        cmd[-1] += f" --public-key {public_key}"
    return subprocess.check_output(cmd).decode().strip()

def install_dozzle(host_ip: str) -> str:
    cmd = ["ssh", f"root@{host_ip}", "curl -sSL https://get.dozzle.io | sh"]
    return subprocess.check_output(cmd).decode().strip()

def install_nomad(host_ip: str) -> str:
    cmd = ["ssh", f"root@{host_ip}", "curl -sSL https://get.nomad.io | sh"]
    return subprocess.check_output(cmd).decode().strip() 