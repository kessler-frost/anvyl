import subprocess
from typing import Optional

def deploy_nomad_job(host_ip: str, job_file: str) -> str:
    cmd = ["ssh", f"root@{host_ip}", f"nomad job run {job_file}"]
    return subprocess.check_output(cmd).decode().strip()

def get_nomad_status(host_ip: str) -> str:
    cmd = ["ssh", f"root@{host_ip}", "nomad server members"]
    return subprocess.check_output(cmd).decode().strip() 