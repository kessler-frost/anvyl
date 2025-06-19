# Anvyl Setup

## Quick Start

**Two simple steps:**

```bash
# 1. Generate protobuf files (one-time setup)
python generate_protos.py

# 2. Install in editable mode
pip install -e .
```

This will:
- ✅ Install all dependencies
- ✅ Set up the `anvyl` CLI command
- ✅ Configure for development (editable mode)
- ✅ Work with the generated protobuf files

## Verify Installation

```bash
# Test the CLI
anvyl --help

# Test the Python SDK
python -c "import anvyl_sdk; print('✅ anvyl_sdk imported successfully')"

# Test protobuf imports
python -c "import generated.anvyl_pb2; print('✅ Protobuf imports working')"
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

## What happens during setup?

1. **Generate protobuf files** - `python generate_protos.py` creates Python files from `protos/anvyl.proto`
2. **Install dependencies** - `pip install -e .` installs from `pyproject.toml` 
3. **CLI setup** - `anvyl` command becomes available globally
4. **Editable mode** - Code changes reflected immediately

## Regenerating Protobuf Files

If you modify the `.proto` file, regenerate the Python files:

```bash
python generate_protos.py
```

## Troubleshooting

If you see import errors:

```bash
# Clean reinstall
pip uninstall anvyl
rm -rf generated/
python generate_protos.py
pip install -e .
```

The `generated/` directory is automatically created and is git-ignored.

## Requirements

- Python 3.12+
- pip
- grpcio-tools (installed automatically)

That's it! Clean, simple, and reliable.