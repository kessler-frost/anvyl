#!/usr/bin/env python3
"""
Anvyl AI Agent Model Providers Example

This example demonstrates how to use different model providers with the Anvyl AI Agent.
Supports LM Studio, Ollama, OpenAI, and Anthropic.
"""

import sys
import os

# Add the parent directory to the path so we can import anvyl
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anvyl.ai_agent import create_ai_agent
from anvyl.model_providers import create_model_provider
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def demo_lmstudio():
    """Demo using LM Studio provider."""
    console.print(Panel(
        "🚀 LM Studio Provider Demo\n\n"
        "Using LM Studio with local MLX models for fast inference.",
        title="LM Studio Demo",
        border_style="blue"
    ))

    try:
        # Create agent with LM Studio (default)
        agent = create_ai_agent("lmstudio", "deepseek/deepseek-r1-0528-qwen3-8b")

        model_info = agent.get_model_info()
        console.print(f"✅ Connected to {model_info['provider']} with {model_info['model_id']}")

        # Test message
        response = agent.chat("What's the system status?")
        console.print(f"Response: {response}")

        return True

    except Exception as e:
        console.print(f"[red]❌ LM Studio Error: {e}[/red]")
        console.print("[yellow]Make sure LM Studio is running with the model loaded[/yellow]")
        return False


def demo_ollama():
    """Demo using Ollama provider."""
    console.print(Panel(
        "🦙 Ollama Provider Demo\n\n"
        "Using Ollama with local models for open-source inference.",
        title="Ollama Demo",
        border_style="green"
    ))

    try:
        # Create agent with Ollama
        agent = create_ai_agent(
            model_provider="ollama",
            model_id="llama3.2",
            agent_name="ollama-agent",
            host="localhost",  # Ollama host
            port=11434,        # Ollama port
            verbose=True
        )

        model_info = agent.get_model_info()
        console.print(f"✅ Connected to {model_info['provider']} with {model_info['model_id']}")

        # Test message
        response = agent.chat("List all hosts")
        console.print(f"Response: {response}")

        return True

    except Exception as e:
        console.print(f"[red]❌ Ollama Error: {e}[/red]")
        console.print("[yellow]Make sure Ollama is running and the model is available[/yellow]")
        console.print("[yellow]Install: curl -fsSL https://ollama.ai/install.sh | sh[/yellow]")
        console.print("[yellow]Run: ollama pull llama3.2[/yellow]")
        return False


def demo_openai():
    """Demo using OpenAI provider."""
    console.print(Panel(
        "🧠 OpenAI Provider Demo\n\n"
        "Using OpenAI GPT models for cloud-based inference.",
        title="OpenAI Demo",
        border_style="cyan"
    ))

    try:
        # Get API key from environment or prompt
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.print("[yellow]No OPENAI_API_KEY environment variable found[/yellow]")
            console.print("[yellow]Set export OPENAI_API_KEY='your-key-here'[/yellow]")
            return False

        # Create agent with OpenAI
        agent = create_ai_agent(
            model_provider="openai",
            model_id="gpt-4o-mini",
            agent_name="openai-agent",
            api_key=api_key,
            verbose=True
        )

        model_info = agent.get_model_info()
        console.print(f"✅ Connected to {model_info['provider']} with {model_info['model_id']}")

        # Test message
        response = agent.chat("Show me all containers")
        console.print(f"Response: {response}")

        return True

    except Exception as e:
        console.print(f"[red]❌ OpenAI Error: {e}[/red]")
        console.print("[yellow]Make sure you have a valid OpenAI API key and credit balance[/yellow]")
        console.print("[yellow]Install: pip install openai[/yellow]")
        return False


def demo_anthropic():
    """Demo using Anthropic provider."""
    console.print(Panel(
        "🤖 Anthropic Provider Demo\n\n"
        "Using Anthropic Claude models for cloud-based inference.",
        title="Anthropic Demo",
        border_style="magenta"
    ))

    try:
        # Get API key from environment or prompt
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            console.print("[yellow]No ANTHROPIC_API_KEY environment variable found[/yellow]")
            console.print("[yellow]Set export ANTHROPIC_API_KEY='your-key-here'[/yellow]")
            return False

        # Create agent with Anthropic
        agent = create_ai_agent(
            model_provider="anthropic",
            model_id="claude-3-haiku-20240307",
            agent_name="anthropic-agent",
            api_key=api_key,
            verbose=True
        )

        model_info = agent.get_model_info()
        console.print(f"✅ Connected to {model_info['provider']} with {model_info['model_id']}")

        # Test message
        response = agent.chat("What agents are running?")
        console.print(f"Response: {response}")

        return True

    except Exception as e:
        console.print(f"[red]❌ Anthropic Error: {e}[/red]")
        console.print("[yellow]Make sure you have a valid Anthropic API key and credit balance[/yellow]")
        console.print("[yellow]Install: pip install anthropic[/yellow]")
        return False


def demo_custom_provider():
    """Demo creating a custom model provider."""
    console.print(Panel(
        "⚙️ Custom Provider Demo\n\n"
        "Creating a custom model provider instance with specific configuration.",
        title="Custom Provider Demo",
        border_style="yellow"
    ))

    try:
        # Create custom provider instance
        provider = create_model_provider(
            provider_type="lmstudio",
            model_id="llama-3.2-3b-instruct-mlx"
        )

        # Create agent with custom provider
        agent = create_ai_agent(
            model_provider=provider,
            agent_name="custom-agent",
            verbose=True
        )

        model_info = agent.get_model_info()
        console.print(f"✅ Using custom {model_info['provider']} with {model_info['model_id']}")

        return True

    except Exception as e:
        console.print(f"[red]❌ Custom Provider Error: {e}[/red]")
        return False


def main():
    """Main demo function."""
    console.print(Panel(
        "🌟 Anvyl AI Agent Model Providers Demo\n\n"
        "This demo shows how to use different model providers with Anvyl AI Agent:\n"
        "• LM Studio (local MLX models)\n"
        "• Ollama (local open-source models)\n"
        "• OpenAI (cloud GPT models)\n"
        "• Anthropic (cloud Claude models)\n"
        "• Custom provider configurations\n\n"
        "Prerequisites:\n"
        "• Anvyl server running (anvyl up)\n"
        "• At least one provider configured",
        title="🤖 Model Providers Demo",
        border_style="bright_blue"
    ))

    # Track results
    results = {}

    console.print("\n" + "="*60)
    console.print("🧪 [bold]Testing Available Providers[/bold]")
    console.print("="*60)

    # Test each provider
    providers = [
        ("LM Studio", demo_lmstudio),
        ("Ollama", demo_ollama),
        ("OpenAI", demo_openai),
        ("Anthropic", demo_anthropic),
        ("Custom", demo_custom_provider),
    ]

    for name, demo_func in providers:
        console.print(f"\n📋 [bold cyan]Testing {name}...[/bold cyan]")
        results[name] = demo_func()
        console.print("\n" + "-"*40)

    # Summary
    console.print(f"\n📊 [bold]Results Summary[/bold]")
    table = Table(title="Provider Test Results")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Notes")

    for name, success in results.items():
        status = "✅ Available" if success else "❌ Not Available"
        notes = ""
        if not success:
            if name == "LM Studio":
                notes = "Install LM Studio and load a model"
            elif name == "Ollama":
                notes = "Install Ollama and pull a model"
            elif name == "OpenAI":
                notes = "Set OPENAI_API_KEY environment variable"
            elif name == "Anthropic":
                notes = "Set ANTHROPIC_API_KEY environment variable"

        table.add_row(name, status, notes)

    console.print(table)

    # Usage examples
    console.print(f"\n💡 [bold]Usage Examples[/bold]")
    console.print("""
CLI Usage:
  # Use LM Studio (default)
  anvyl agent chat my-ai "show hosts"

  # Use Ollama
  anvyl agent chat my-ai "show hosts" --provider ollama --model llama3.2

  # Use OpenAI
  anvyl agent chat my-ai "show hosts" --provider openai --model gpt-4o-mini --api-key YOUR_KEY

  # Use Anthropic
  anvyl agent chat my-ai "show hosts" --provider anthropic --model claude-3-haiku-20240307 --api-key YOUR_KEY

Python API:
  from anvyl.ai_agent import create_ai_agent

  # LM Studio
  agent = create_ai_agent("lmstudio", "llama-3.2-1b-instruct-mlx")

  # Ollama
  agent = create_ai_agent("ollama", "llama3.2", host="localhost", port=11434)

  # OpenAI
  agent = create_ai_agent("openai", "gpt-4o-mini", api_key="your-key")

  # Anthropic
  agent = create_ai_agent("anthropic", "claude-3-haiku-20240307", api_key="your-key")
    """)

    successful_providers = [name for name, success in results.items() if success]
    if successful_providers:
        console.print(f"\n🎉 [bold green]Success! You can use these providers: {', '.join(successful_providers)}[/bold green]")
    else:
        console.print(f"\n⚠️ [bold yellow]No providers are currently available. Please configure at least one.[/bold yellow]")

    return len(successful_providers) > 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        sys.exit(1)