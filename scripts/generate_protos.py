#!/usr/bin/env python3
"""
Script to generate protobuf files for Anvyl.
This ensures consistent generation with proper imports.
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    """Generate protobuf files from .proto definitions."""
    
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Create generated directory
    generated_dir = project_root / "generated"
    generated_dir.mkdir(exist_ok=True)
    
    # Generate protobuf files
    proto_file = "protos/anvyl.proto"
    
    if not Path(proto_file).exists():
        print(f"❌ Error: {proto_file} not found!")
        sys.exit(1)
    
    print("🔄 Generating protobuf files...")
    
    try:
        # Generate Python protobuf files
        subprocess.run([
            sys.executable, "-m", "grpc_tools.protoc",
            "--python_out=generated",
            "--grpc_python_out=generated", 
            "--proto_path=protos",
            proto_file
        ], check=True)
        
        # Create __init__.py
        init_file = generated_dir / "__init__.py"
        init_file.touch()
        
        # Fix import in gRPC file
        grpc_file = generated_dir / "anvyl_pb2_grpc.py"
        if grpc_file.exists():
            content = grpc_file.read_text()
            content = content.replace(
                "import anvyl_pb2 as anvyl__pb2",
                "from . import anvyl_pb2 as anvyl__pb2"
            )
            grpc_file.write_text(content)
            print("🔧 Fixed import in anvyl_pb2_grpc.py")
        
        print("✅ Protobuf files generated successfully!")
        print(f"   📁 Generated files in: {generated_dir}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating protobuf files: {e}")
        print("💡 Make sure you have grpcio-tools installed:")
        print("   pip install grpcio-tools>=1.59.0")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()