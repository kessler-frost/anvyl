from pyinfra.operations import server, files

def install_dozzle(ip: str):
    return server.shell(
        name=f"Install Dozzle on {ip}",
        commands=[
            "docker rm -f dozzle || true",
            "docker pull amir20/dozzle",
            "docker run -d --name dozzle -p 8888:8080 "
            "-v /var/lib/docker/containers:/var/lib/docker/containers:ro "
            "amir20/dozzle"
        ],
        hosts=[ip],
        ssh_user="root"
    )

def install_beszel(ip: str, public_key: str):
    download_url = (
        "https://github.com/henrygd/beszel/releases/latest/download/"
        "beszel-agent_$(uname -s)_$(uname -m).tar.gz"
    )
    return [
        files.download(
            name=f"Download Beszel agent on {ip}",
            src=download_url,
            dest="/tmp/beszel-agent.tar.gz",
            hosts=[ip],
            ssh_user="root",
        ),
        server.shell(
            name="Extract and install Beszel",
            commands=[
                "tar -xz -f /tmp/beszel-agent.tar.gz -C /usr/local/bin beszel-agent",
                "chmod +x /usr/local/bin/beszel-agent",
            ],
            hosts=[ip],
            ssh_user="root",
        ),
        server.shell(
            name="Create beszel-agent systemd service",
            commands=[
                'cat > /etc/systemd/system/beszel-agent.service <<EOF\n'
                '[Unit]\n'
                'Description=Beszel Agent Service\n'
                'After=network-online.target\n'
                'Wants=network-online.target\n\n'
                '[Service]\n'
                f'ExecStart=/usr/local/bin/beszel-agent -listen "45876" -key "{public_key}"\n'
                'Restart=on-failure\n\n'
                '[Install]\n'
                'WantedBy=multi-user.target\n'
                'EOF'
            ],
            hosts=[ip],
            ssh_user="root",
        ),
        server.shell(
            name="Enable and start beszel-agent",
            commands=[
                "systemctl daemon-reload",
                "systemctl enable beszel-agent",
                "systemctl start beszel-agent"
            ],
            hosts=[ip],
            ssh_user="root",
        ),
    ]

def install_nomad(ip: str):
    return server.shell(
        name=f"Install Nomad on {ip}",
        commands=[
            "curl -fsSL https://releases.hashicorp.com/nomad/1.7.4/nomad_1.7.4_linux_amd64.zip -o nomad.zip",
            "unzip -o nomad.zip -d /usr/local/bin",
            "chmod +x /usr/local/bin/nomad",
            "rm nomad.zip",
            "mkdir -p /etc/nomad.d",
            "chmod 700 /etc/nomad.d",
            "echo '{\"server\": {\"enabled\": true, \"bootstrap_expect\": 1}, \"datacenter\": \"sindri\"}' > /etc/nomad.d/nomad.hcl",
            'cat > /etc/systemd/system/nomad.service <<EOF\n'
            '[Unit]\n'
            'Description=Nomad\n'
            'After=network.target\n\n'
            '[Service]\n'
            'ExecStart=/usr/local/bin/nomad agent -config=/etc/nomad.d\n'
            'Restart=on-failure\n\n'
            '[Install]\n'
            'WantedBy=multi-user.target\n'
            'EOF',
            "systemctl daemon-reload",
            "systemctl enable nomad",
            "systemctl start nomad"
        ],
        hosts=[ip],
        ssh_user="root",
    )
