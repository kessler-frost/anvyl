#!/usr/bin/env python3
"""
Anvyl AI Agent Example

This example demonstrates how to use the Anvyl AI Agent with LMStudio's act() function
to manage infrastructure using natural language.
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
        f"🚀 Anvyl AI Agent Example (Agent: {agent_name})\n\n"
        "This example shows how to use LMStudio's act() function with Anvyl's gRPC client\n"
        "to manage infrastructure using natural language commands.",
        title=f"🤖 AI Agent Demo: {agent_name}",
        border_style="blue"
    ))
    
    try:
        # Create AI agent
        console.print(f"🔧 [bold blue]Creating AI Agent '{agent_name}'...[/bold blue]")
        agent = create_ai_agent(
            model_id="llama-3.2-1b-instruct-mlx",
            host="localhost",
            port=50051,
            verbose=True,
            agent_name=agent_name
        )
        
        console.print(f"✅ [bold green]AI Agent '{agent_name}' created successfully![/bold green]")
        
        # Example interactions
        examples = [
            "What's the current system status?",
            "Show me all hosts in the infrastructure",
            "List all running containers",
            "Create a simple nginx container named 'web-server'",
            "What agents are currently running?"
        ]
        
        console.print("\n📝 [bold yellow]Running Example Interactions:[/bold yellow]")
        
        for i, message in enumerate(examples, 1):
            console.print(f"\n[bold cyan]Example {i}:[/bold cyan] {message}")
            console.print("[bold blue]AI Response:[/bold blue]")
            
            try:
                response = agent.chat(message)
                console.print(response)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            
            if i < len(examples):
                console.print("\n" + "─" * 60)
        
        console.print(f"\n🎉 [bold green]Example completed successfully for agent '{agent_name}'![bold green]")
        console.print("\n💡 [bold]Next Steps:[/bold]")
        console.print(f"  • Try the interactive mode: anvyl agent interactive {agent_name}")
        console.print(f"  • Use single commands: anvyl agent chat {agent_name} 'your message'")
        console.print(f"  • Run the demo: anvyl agent demo {agent_name}")
        
    except ImportError as e:
        console.print(f"[red]❌ Import Error: {e}[/red]")
        console.print("[yellow]Make sure LMStudio is installed: pip install lmstudio[/yellow]")
        return False
    except ConnectionError as e:
        console.print(f"[red]❌ Connection Error: {e}[/red]")
        console.print("[yellow]Make sure the Anvyl gRPC server is running: anvyl up[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Unexpected Error: {e}[/red]")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 