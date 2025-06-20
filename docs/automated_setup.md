# Automated Proto Generation Setup

## Overview

The project has been configured to automatically generate protocol buffer files during the `pip install` process using modern Python packaging standards. You no longer need to manually run `python generate_protos.py` before installing the package.

## Modern Approach - Why No setup.py

This implementation follows modern Python packaging best practices by:

- **Using `pyproject.toml`** - All configuration is in the standard `pyproject.toml` file
- **No `setup.py`** - Avoiding the deprecated `setup.py` approach  
- **Modern setuptools** - Using setuptools>=64 with proper pyproject.toml configuration
- **Build hooks** - Custom commands configured declaratively in `pyproject.toml`

## Changes Made

### 1. Modern Build Configuration (`pyproject.toml`)

The build system is configured in `pyproject.toml` with:

- **Build Requirements**: `grpcio-tools>=1.59.0` and `protobuf>=4.21.0` in `build-system.requires`
- **Custom Commands**: `tool.setuptools.cmdclass` defines custom build and develop commands
- **Package Discovery**: Modern setuptools configuration for package and module discovery
- **No setup.py**: Everything is configured declaratively in `pyproject.toml`

### 2. Build Hook Module (`build_proto_hook.py`)

A dedicated build hook module that:

- **Modern Structure**: Separate module (not setup.py) with clear separation of concerns
- **Mixin Pattern**: Reusable `ProtocolBufferMixin` for proto generation logic
- **Multiple Commands**: Supports both `build_py` (regular install) and `develop` (editable install)
- **Error Handling**: Comprehensive error handling and user feedback

### 3. Updated Scripts

The `generate_protos.py` script remains as a development fallback tool.

## How It Works

### During Installation (`pip install -e .`)

1. **Build System**: pip reads `pyproject.toml` and sets up the modern build environment
2. **Dependencies**: Build dependencies (`grpcio-tools`, `protobuf`) are automatically installed
3. **Custom Commands**: setuptools uses the custom commands defined in `pyproject.toml`:
   - `BuildPyCommand` for regular installations
   - `DevelopCommand` for editable installs (`-e`)
4. **Proto Generation**: The build hook automatically:
   - Checks for `protos/anvyl.proto`
   - Creates the `generated/` directory
   - Runs `grpc_tools.protoc` to generate Python files
   - Fixes import statements in generated gRPC files
   - Creates `__init__.py` in the generated package
5. **Package Building**: Standard setuptools build continues with generated files included

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

## Modern Packaging Benefits

1. **Standards Compliant**: Follows PEP 517/518 modern build standards
2. **No setup.py**: Eliminates the deprecated setup.py approach
3. **Declarative Config**: All configuration in `pyproject.toml`
4. **Tool Compatibility**: Works with modern tools like `build`, `pip`, and package managers
5. **CI/CD Friendly**: Standard build process that works everywhere
6. **Maintainable**: Clear separation of build logic from configuration

## Technical Details

### Configuration Structure
```toml
[build-system]
requires = ["setuptools>=64", "wheel", "grpcio-tools>=1.59.0", "protobuf>=4.21.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.cmdclass]
build_py = "build_proto_hook:BuildPyCommand"
develop = "build_proto_hook:DevelopCommand"
```

### Build Hook Module
- **Mixin Design**: Reusable proto generation logic
- **Command Classes**: Extend standard setuptools commands
- **Error Handling**: Proper error messages and exit codes

## Troubleshooting

If you encounter issues:

1. **Build Failures**: Check that `grpcio-tools` is available in build environment
2. **Import Errors**: Ensure the `generated` package is being included in your installation
3. **Development**: Use `python generate_protos.py` for quick iteration during development
4. **Modern Tools**: This works with `python -m build`, `pip install`, and other modern tools

The automated setup ensures that proto generation happens seamlessly as part of the modern Python package installation process, without requiring any deprecated setup.py files.