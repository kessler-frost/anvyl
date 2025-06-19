#!/usr/bin/env python3
"""
Custom setup.py to generate protobuf files during build.
"""

import subprocess
import sys
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildPyCommand(build_py):
    """Custom build command that generates protobuf files."""
    
    def run(self):
        """Run the build process with proto generation."""
        self.generate_protos()
        super().run()
    
    def generate_protos(self):
        """Generate protobuf files."""
        project_root = Path(__file__).parent
        
        # Check for proto file
        proto_file = project_root / "protos" / "anvyl.proto"
        if not proto_file.exists():
            print(f"❌ Error: {proto_file} not found!")
            sys.exit(1)
        
        # Create generated directory
        generated_dir = project_root / "generated"
        generated_dir.mkdir(exist_ok=True)
        
        print("🔄 Generating protobuf files...")
        
        try:
            # Generate protobuf files
            subprocess.run([
                sys.executable, "-m", "grpc_tools.protoc",
                "--python_out=generated",
                "--grpc_python_out=generated", 
                "--proto_path=protos",
                "protos/anvyl.proto"
            ], check=True)
            
            # Create __init__.py
            (generated_dir / "__init__.py").touch()
            
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
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error generating protobuf files: {e}")
            print("💡 Make sure you have grpcio-tools installed:")
            print("   pip install grpcio-tools")
            sys.exit(1)


if __name__ == "__main__":
    setup(
        cmdclass={
            'build_py': BuildPyCommand,
        }
    )