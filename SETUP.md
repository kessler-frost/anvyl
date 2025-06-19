# Anvyl Setup

## Quick Start

**That's it! Just run:**

```bash
pip install -e .
```

This will automatically:
- ✅ Install all dependencies
- ✅ Generate protobuf files from `.proto` definitions  
- ✅ Set up the `anvyl` CLI command
- ✅ Configure for development (editable mode)

## Verify Installation

```bash
# Test the CLI
anvyl --help

# Test the Python SDK
python -c "import anvyl_sdk; print('✅ anvyl_sdk imported successfully')"
```

## Development

After installation, you can immediately start developing:

```bash
# Make code changes and they'll be reflected immediately (editable install)
# No need to reinstall

# Run the CLI
anvyl up

# Or import in Python
python -c "from anvyl_sdk import AnvylClient"
```

## What happens automatically?

When you run `pip install -e .`, the build system:

1. **Installs dependencies** from `pyproject.toml` 
2. **Generates protobuf files** from `protos/anvyl.proto` into `generated/`
3. **Fixes import statements** in generated gRPC files
4. **Sets up CLI commands** (`anvyl` command available globally)
5. **Configures editable mode** (code changes reflected immediately)

## Manual Protobuf Generation (Optional)

If you need to regenerate protobuf files manually during development:

```bash
python generate_protos.py
```

This is usually not needed since protobuf files are auto-generated during installation.

## Troubleshooting

If you see import errors:

```bash
# Clean reinstall
pip uninstall anvyl
rm -rf generated/
pip install -e .
```

If the automatic generation fails, use the manual fallback:

```bash
python generate_protos.py
pip install -e .
```

The `generated/` directory is automatically created and is git-ignored.

## Requirements

- Python 3.12+
- pip

That's it! No separate scripts, no manual protobuf generation, no complex setup.