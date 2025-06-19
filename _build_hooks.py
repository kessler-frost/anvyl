"""
Build hooks for Anvyl - automatically generates protobuf files during installation.
"""

import os
import subprocess
import sys
from pathlib import Path

from setuptools.command.build_py import build_py
from setuptools.command.develop import develop


def generate_protobuf_files():
    """Generate protobuf files from .proto definitions."""
    
    # Get current directory (should be project root during build)
    project_root = Path.cwd()
    
    # Ensure we're in the right place
    proto_file = project_root / "protos" / "anvyl.proto"
    if not proto_file.exists():
        print(f"⚠️  Warning: {proto_file} not found, skipping protobuf generation")
        return False
    
    # Create generated directory
    generated_dir = project_root / "generated"
    generated_dir.mkdir(exist_ok=True)
    
    print("🔄 Auto-generating protobuf files...")
    
    try:
        # Generate Python protobuf files
        result = subprocess.run([
            sys.executable, "-m", "grpc_tools.protoc",
            "--python_out=generated",
            "--grpc_python_out=generated", 
            "--proto_path=protos",
            "protos/anvyl.proto"
        ], check=True, capture_output=True, text=True)
        
        # Create __init__.py
        init_file = generated_dir / "__init__.py"
        init_file.touch()
        
        # Fix import in gRPC file
        grpc_file = generated_dir / "anvyl_pb2_grpc.py"
        if grpc_file.exists():
            content = grpc_file.read_text()
            if "import anvyl_pb2 as anvyl__pb2" in content:
                content = content.replace(
                    "import anvyl_pb2 as anvyl__pb2",
                    "from . import anvyl_pb2 as anvyl__pb2"
                )
                grpc_file.write_text(content)
        
        print("✅ Protobuf files generated successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: Could not generate protobuf files")
        print(f"    Command: {' '.join(e.cmd)}")
        print(f"    Return code: {e.returncode}")
        if e.stdout:
            print(f"    Stdout: {e.stdout}")
        if e.stderr:
            print(f"    Stderr: {e.stderr}")
        print("💡 Make sure grpcio-tools is installed")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error generating protobuf files: {e}")
        return False


class BuildPyWithProtos(build_py):
    """Custom build_py that generates protobuf files first."""
    
    def run(self):
        # Generate protobuf files before building
        generate_protobuf_files()
        # Run the normal build
        super().run()


class DevelopWithProtos(develop):
    """Custom develop that generates protobuf files for editable installs."""
    
    def run(self):
        # Generate protobuf files before installing in develop mode
        generate_protobuf_files()
        # Run the normal develop install
        super().run()


if __name__ == "__main__":
    # Can also be run standalone for manual generation
    success = generate_protobuf_files()
    sys.exit(0 if success else 1)