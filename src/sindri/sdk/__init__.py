"""
SDK package for Sindri
"""

from .install_agents import install_beszel, install_dozzle, install_nomad
from .homelab_nomad import deploy_nomad_job, get_nomad_status 