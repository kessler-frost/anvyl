"""
Utility module for automatic protobuf generation.
This ensures protobuf files are generated automatically when needed.
"""

import subprocess
import sys
from pathlib import Path


def ensure_protos_generated():
    """Ensure protobuf files are generated, generating them if necessary."""
    project_root = Path(__file__).parent
    generated_dir = project_root / "generated"
    
    # Check if protobuf files already exist
    pb2_file = generated_dir / "anvyl_pb2.py"
    grpc_file = generated_dir / "anvyl_pb2_grpc.py"
    
    if pb2_file.exists() and grpc_file.exists():
        # Files already exist, no need to regenerate
        return
    
    # Generate protobuf files
    print("🔄 Auto-generating protobuf files...")
    
    # Check for proto file
    proto_file = project_root / "protos" / "anvyl.proto"
    if not proto_file.exists():
        print(f"❌ Error: {proto_file} not found!")
        return
    
    # Create generated directory
    generated_dir.mkdir(exist_ok=True)
    
    try:
        # Generate protobuf files
        subprocess.run([
            sys.executable, "-m", "grpc_tools.protoc",
            "--python_out=generated",
            "--grpc_python_out=generated", 
            "--proto_path=protos",
            "protos/anvyl.proto"
        ], check=True, cwd=project_root)
        
        # Create __init__.py
        (generated_dir / "__init__.py").touch()
        
        # Fix import in gRPC file
        if grpc_file.exists():
            content = grpc_file.read_text()
            if "import anvyl_pb2 as anvyl__pb2" in content:
                content = content.replace(
                    "import anvyl_pb2 as anvyl__pb2",
                    "from . import anvyl_pb2 as anvyl__pb2"
                )
                grpc_file.write_text(content)
        
        print("✅ Protobuf files auto-generated successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error auto-generating protobuf files: {e}")
        print("💡 Make sure you have grpcio-tools installed:")
        print("   pip install grpcio-tools")
    except Exception as e:
        print(f"❌ Unexpected error during proto generation: {e}")