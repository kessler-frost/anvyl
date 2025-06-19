# Anvyl Installation Guide

This guide covers different ways to install Anvyl as a Python package.

## System Requirements

- **Python**: 3.12 or higher
- **Operating System**: macOS 15+ (primary target) or Linux
- **Docker**: Required for container management
- **Protobuf Compiler**: Required for development (installed automatically)

## Installation Options

### Option 1: Install from PyPI (Recommended)

Once published to PyPI, you can install Anvyl with:

```bash
pip install anvyl
```

### Option 2: Install from Source (Current)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kessler-frost/anvyl.git
   cd anvyl
   ```

2. **Install the package:**
   ```bash
   pip install .
   ```

3. **Or install in development mode:**
   ```bash
   pip install -e .
   ```

### Option 3: Install from Distribution Files

If you have the distribution files (`.whl` or `.tar.gz`):

```bash
# Install from wheel (recommended)
pip install anvyl-0.1.0-py3-none-any.whl

# Or install from tarball
pip install anvyl-0.1.0.tar.gz
```

### Option 4: Install with Development Dependencies

For development work:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Or install all optional dependencies
pip install -e ".[all]"
```

## Installation Verification

After installation, verify that Anvyl is working:

```bash
# Check if the CLI is available
anvyl --help

# Check version
anvyl version

# Test basic functionality
anvyl status
```

## Development Setup

For contributors and developers:

1. **Clone and set up development environment:**
   ```bash
   git clone https://github.com/kessler-frost/anvyl.git
   cd anvyl
   ./scripts/dev_setup.sh
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install in development mode:**
   ```bash
   pip install -e ".[dev]"
   ```

## Docker Requirements

Anvyl requires Docker for container management. Install Docker based on your platform:

### macOS
```bash
# Install Docker Desktop
brew install --cask docker
```

### Linux
```bash
# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

## Troubleshooting

### Common Issues

1. **Python Version Error**
   ```
   ERROR: Package requires Python >=3.12
   ```
   **Solution**: Install Python 3.12 or higher

2. **gRPC Installation Issues**
   ```
   ERROR: Failed building wheel for grpcio
   ```
   **Solution**: Install system dependencies
   ```bash
   # macOS
   brew install protobuf
   
   # Linux
   sudo apt-get install protobuf-compiler
   ```

3. **Permission Errors**
   ```
   ERROR: Permission denied
   ```
   **Solution**: Use virtual environment or `--user` flag
   ```bash
   pip install --user anvyl
   ```

4. **CLI Not Found**
   ```
   command not found: anvyl
   ```
   **Solution**: Check if the installation directory is in your PATH
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$HOME/.local/bin:$PATH"
   ```

### Getting Help

- **Documentation**: [README.md](README.md)
- **CLI Help**: `anvyl --help`
- **Issues**: [GitHub Issues](https://github.com/kessler-frost/anvyl/issues)

## Uninstallation

To remove Anvyl:

```bash
pip uninstall anvyl
```

## Package Structure

After installation, Anvyl provides:

- **CLI Tool**: `anvyl` command-line interface
- **Python SDK**: `anvyl_sdk` package for programmatic use
- **Database Models**: `database` package for data persistence
- **gRPC Bindings**: `generated` package for protocol buffer definitions

## Usage Examples

### Basic CLI Usage
```bash
# Start the infrastructure
anvyl up

# List containers
anvyl container list

# Create a container
anvyl container create web nginx:alpine --port 8080:80

# View logs
anvyl logs frontend -f
```

### Python SDK Usage
```python
from anvyl_sdk import create_client

# Connect to Anvyl
client = create_client("localhost", 50051)

# List hosts
hosts = client.list_hosts()
print(f"Found {len(hosts)} hosts")

# Disconnect
client.disconnect()
```

## Next Steps

1. **Read the Documentation**: Check [README.md](README.md) for detailed usage
2. **Start the Services**: Run `anvyl up` to start the infrastructure
3. **Explore the CLI**: Use `anvyl --help` to see all available commands
4. **Access the Web UI**: Open http://localhost:3000 after running `anvyl up`

---

For more information, see the [project documentation](https://github.com/kessler-frost/anvyl#readme).