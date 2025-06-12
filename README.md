# Sindri

<p align="center">
  <b>Code-first control of self-hosted, containerized infrastructure — across your realm.</b><br>
  <img alt="License" src="https://img.shields.io/badge/license-Apache%202.0-blue">
  <img alt="Python" src="https://img.shields.io/badge/python-3.12-blue">
  <img alt="Build" src="https://img.shields.io/badge/build-passing-brightgreen">
</p>

Sindri is a programmable infrastructure orchestrator built for small-scale, self-hosted clusters. It leverages a secure mesh (via Netbird), declarative provisioning (via pyinfra), and powerful job scheduling (via Nomad), all wrapped in a Python-first developer experience.

---

## ✨ Features

- 🚀 REST API to manage hosts (Netbird-connected)
- 💾 Persistent state with SQLite + SQLModel
- 🔧 Provisioning via Pyinfra
- 🧠 FastAPI backend with UI-ready design
- 🔐 Secure mesh communication (Netbird)
- 📊 Logs and metrics via Dozzle & Beszel (soon)

---

## 🛠 Tech Stack

![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLModel](https://img.shields.io/badge/-SQLModel-3D5AFE?style=flat-square)
![Nomad](https://img.shields.io/badge/-Nomad-000000?style=flat-square&logo=hashicorp&logoColor=white)
![Pyinfra](https://img.shields.io/badge/-Pyinfra-444444?style=flat-square)
![Netbird](https://img.shields.io/badge/-Netbird-0080FF?style=flat-square)

---

## 🔧 Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

# Start FastAPI
fastapi dev main:app
```

---

## 📦 Roadmap

- [ ] Install Dozzle + Beszel agents
- [ ] Nomad job deployment via API
- [ ] Cluster-wide logging & metrics
- [ ] Web dashboard UI ("Realm")
- [ ] Secrets management
- [ ] Traefik integration
