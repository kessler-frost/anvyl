#!/usr/bin/env python3
"""
Simple script to manually generate protobuf files.
This is a fallback - protobuf files are now generated automatically during pip install.
You should only need to run this script directly if you're doing development work
and need to regenerate the protos without reinstalling the package.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Generate protobuf files manually."""
    
    project_root = Path(__file__).parent
    
    # Check for proto file
    proto_file = project_root / "protos" / "anvyl.proto"
    if not proto_file.exists():
        print(f"❌ Error: {proto_file} not found!")
        return 1
    
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
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating protobuf files: {e}")
        print("💡 Make sure you have grpcio-tools installed:")
        print("   pip install grpcio-tools")
        return 1


if __name__ == "__main__":
    sys.exit(main())