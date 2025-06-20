#!/usr/bin/env python3
"""
Anvyl AI Agent Example

This example demonstrates how to use the Anvyl AI Agent with configurable model providers
to execute infrastructure management tasks using natural language instructions.
"""

import sys
import os

if len(sys.argv) < 2:
    print("Usage: python ai_agent_example.py <agent_name>")
    sys.exit(1)

agent_name = sys.argv[1]

# Add the parent directory to the path so we can import anvyl
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anvyl.ai_agent import create_ai_agent
from rich.console import Console
from rich.panel import Panel

console = Console()


def main():
    """Main example function."""
    console.print(Panel(
        f"🚀 Anvyl AI Agent Action Example (Agent: {agent_name})\n\n"
        "This example shows how to use configurable model providers with Anvyl's gRPC client\n"
        "to execute infrastructure management tasks using natural language instructions.",
        title=f"🤖 AI Agent Action Demo: {agent_name}",
        border_style="blue"
    ))

    try:
        console.print("\n🔧 [bold yellow]Initializing AI Agent...[/bold yellow]")

        # Create AI agent with default LM Studio provider
        agent = create_ai_agent(
            model_provider="lmstudio",  # Can also use "ollama", "openai", "anthropic"
            model_id="llama-3.2-1b-instruct-mlx",
            agent_name=agent_name,
            verbose=True
        )

        model_info = agent.get_model_info()
        console.print(f"✅ [bold green]Agent initialized successfully![/bold green]")
        console.print(f"   Provider: {model_info['provider']}")
        console.print(f"   Model: {model_info['model_id']}")
        console.print(f"   Agent Name: {agent_name}")

        # Show available actions
        console.print(f"\n📋 [bold yellow]Available Actions:[/bold yellow]")
        actions = agent.get_available_actions()
        for action in actions[:5]:  # Show first 5 actions
            console.print(f"  • {action}")
        console.print(f"  ... and {len(actions) - 5} more actions")

        # Example instructions to demonstrate capabilities
        example_instructions = [
            "Show me the current system status",
            "List all hosts in the infrastructure",
            "Get information about running containers",
            "Display all available agents",
            "Check the UI stack status"
        ]

        console.print("\n📝 [bold yellow]Running Example Instructions:[/bold yellow]")

        for i, instruction in enumerate(example_instructions, 1):
            console.print(f"\n[bold cyan]Instruction {i}:[/bold cyan] {instruction}")
            console.print("[bold blue]🔄 Executing...[/bold blue]")

            try:
                result = agent.act(instruction)
                console.print(f"[bold green]✅ Result:[/bold green] {result}")
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")

            if i < len(example_instructions):
                console.print("\n" + "─" * 60)

        console.print(f"\n🎉 [bold green]Example completed successfully for agent '{agent_name}'![bold green]")
        console.print("\n💡 [bold]Next Steps:[/bold]")
        console.print(f"  • Try the interactive mode: anvyl agent session {agent_name}")
        console.print(f"  • Execute single instructions: anvyl agent act {agent_name} 'your instruction'")
        console.print(f"  • Run the demo: anvyl agent demo {agent_name}")
        console.print(f"  • List all available agents: anvyl agent list")
        console.print(f"  • See available actions: anvyl agent actions {agent_name}")

        # Example of using different providers
        console.print(f"\n🔄 [bold]Provider Examples:[/bold]")
        console.print("  # Use LM Studio (default)")
        console.print(f"  anvyl agent act {agent_name} 'show hosts'")
        console.print("  # Use Ollama")
        console.print(f"  anvyl agent act {agent_name} 'show hosts' --provider ollama --model llama3.2")
        console.print("  # Use OpenAI")
        console.print(f"  anvyl agent act {agent_name} 'show hosts' --provider openai --model gpt-4o-mini --api-key YOUR_KEY")

    except ImportError as e:
        console.print(f"[red]❌ Import Error: {e}[/red]")
        console.print("[yellow]Make sure the required model provider is installed[/yellow]")
        console.print("[yellow]LM Studio: pip install lmstudio[/yellow]")
        console.print("[yellow]Ollama: Install from https://ollama.ai[/yellow]")
        console.print("[yellow]OpenAI: pip install openai[/yellow]")
        console.print("[yellow]Anthropic: pip install anthropic[/yellow]")
        return False
    except ConnectionError as e:
        console.print(f"[red]❌ Connection Error: {e}[/red]")
        console.print("[yellow]Make sure the Anvyl gRPC server is running: anvyl up[/yellow]")
        console.print("[yellow]Make sure your model provider is available and configured[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Unexpected Error: {e}[/red]")
        return False

    return True


def interactive_example():
    """Example of interactive action session."""
    console.print(Panel(
        f"🔄 Interactive Action Session Example\n\n"
        "You can also start an interactive session where you can give\n"
        "instructions continuously and see results in real-time.",
        title=f"Interactive Mode: {agent_name}",
        border_style="green"
    ))

    try:
        agent = create_ai_agent(agent_name=agent_name, verbose=True)

        console.print("\n💡 [bold]Starting interactive session...[/bold]")
        console.print("[bold]Commands:[/bold]")
        console.print("  • Type any natural language instruction")
        console.print("  • 'help' - Show available commands")
        console.print("  • 'actions' - Show available actions")
        console.print("  • 'quit' - Exit session")

        # Start interactive session
        agent.interactive_action_session()

    except Exception as e:
        console.print(f"[red]❌ Error starting interactive session: {e}[/red]")


if __name__ == "__main__":
    try:
        # Run main example
        success = main()

        if success:
            # Ask if user wants to try interactive mode
            try:
                response = console.input("\n[bold cyan]Would you like to try interactive mode? (y/n):[/bold cyan] ")
                if response.lower() in ['y', 'yes']:
                    interactive_example()
            except KeyboardInterrupt:
                console.print("\n[yellow]Skipping interactive mode.[/yellow]")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Example interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        sys.exit(1)