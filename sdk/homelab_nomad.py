from pyinfra.api import deploy
from pyinfra.operations import apt, files, server

@deploy("Install core packages")
def install_base_packages():
    apt.packages(
        name="Install Docker, unzip, and curl",
        packages=["docker.io", "unzip", "curl"],
        update=True
    )

@deploy("Install Nomad binary")
def install_nomad():
    files.download(
        name="Download Nomad binary",
        src="https://releases.hashicorp.com/nomad/1.7.5/nomad_1.7.5_linux_amd64.zip",
        dest="/tmp/nomad.zip"
    )
    server.shell(
        name="Install Nomad",
        commands=[
            "unzip -o /tmp/nomad.zip -d /usr/local/bin",
            "chmod +x /usr/local/bin/nomad"
        ]
    )

@deploy("Configure Nomad")
def configure_nomad():
    files.template(
        name="Write Nomad config",
        src="templates/nomad.hcl.j2",
        dest="/etc/nomad.d/nomad.hcl"
    )
    server.shell(
        name="Enable and start Nomad",
        commands=[
            "mkdir -p /etc/nomad.d",
            "nomad agent -config /etc/nomad.d/nomad.hcl &"
        ]
    )
