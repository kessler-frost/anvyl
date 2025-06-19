# Automated Proto Generation Setup

## Overview

The project has been configured to automatically generate protocol buffer files during the `pip install` process. You no longer need to manually run `python generate_protos.py` before installing the package.

## Changes Made

### 1. Custom Setup Script (`setup.py`)

A custom `setup.py` file has been added that extends the setuptools build process:

- **Custom Build Command**: Extends `setuptools.command.build_py.build_py` to run proto generation before building Python packages
- **Automatic Proto Generation**: Runs the same logic as `generate_protos.py` but integrated into the build process
- **Error Handling**: Provides clear error messages if proto generation fails

### 2. Build System Configuration

The `pyproject.toml` already had the correct configuration:

- **Build Requirements**: `grpcio-tools>=1.59.0` and `protobuf>=4.21.0` are specified in `build-system.requires`
- **Package Discovery**: The `generated` package is included in `setuptools.packages.find.include`
- **Dependencies**: Runtime dependencies include the necessary gRPC packages

### 3. Updated Scripts

The `generate_protos.py` script has been updated to clarify that it's now a fallback for development use only.

## How It Works

### During Installation (`pip install -e .`)

1. **Dependency Resolution**: pip installs build dependencies (`grpcio-tools`, `protobuf`, etc.)
2. **Custom Build**: The custom `BuildPyCommand` class runs the proto generation:
   - Checks for `protos/anvyl.proto`
   - Creates the `generated/` directory
   - Runs `grpc_tools.protoc` to generate Python files
   - Fixes import statements in generated gRPC files
   - Creates `__init__.py` in the generated package
3. **Package Building**: Standard setuptools build process continues with generated files included

### What Gets Generated

- `generated/anvyl_pb2.py` - Protocol buffer message classes
- `generated/anvyl_pb2_grpc.py` - gRPC service stubs and client classes  
- `generated/__init__.py` - Makes it a proper Python package

## Usage

### Standard Installation
```bash
# This now works without any manual steps!
pip install -e .
```

### Development Usage
```bash
# For development, you can still manually regenerate protos if needed
python generate_protos.py

# Or just reinstall to regenerate everything
pip install -e . --force-reinstall
```

## Benefits

1. **Simplified Workflow**: No more manual proto generation step
2. **Consistent Builds**: Proto files are always regenerated from source during installation
3. **CI/CD Friendly**: Build pipelines don't need special proto generation steps
4. **Version Control**: Generated files can be safely excluded from git (they're recreated automatically)
5. **Error Prevention**: Can't forget to regenerate protos when proto files change

## Troubleshooting

If you encounter issues:

1. **Build Failures**: Check that `grpcio-tools` is available in build environment
2. **Import Errors**: Ensure the `generated` package is being included in your installation
3. **Development**: Use `python generate_protos.py` for quick iteration during development

The automated setup ensures that proto generation happens seamlessly as part of the normal Python package installation process.