"""
Model Provider Abstraction

This module provides an abstract interface for different model providers,
allowing easy switching between LM Studio, Ollama, and cloud-based alternatives.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class ModelProvider(ABC):
    """Abstract base class for model providers."""

    def __init__(self, model_id: str, **kwargs):
        """
        Initialize the model provider.

        Args:
            model_id: The model identifier/name
            **kwargs: Provider-specific configuration
        """
        self.model_id = model_id
        self.config = kwargs

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize and connect to the model provider.

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def act(self, instruction: str, available_actions: Optional[List[Callable]] = None, **kwargs) -> str:
        """
        Execute an instruction by determining and performing appropriate actions.

        Args:
            instruction: The instruction/task to execute
            available_actions: Optional list of available actions for the agent
            **kwargs: Additional provider-specific parameters

        Returns:
            Result of the action execution
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the model provider is available.

        Returns:
            True if available, False otherwise
        """
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_id": self.model_id,
            "provider": self.__class__.__name__,
            "config": self.config
        }


class LMStudioProvider(ModelProvider):
    """LM Studio provider for local MLX models."""

    def __init__(self, model_id: str = "deepseek/deepseek-r1-0528-qwen3-8b", host: str = "localhost", **kwargs):
        """
        Initialize LM Studio provider.

        Args:
            model_id: LM Studio model identifier
            host: LM Studio server host
            **kwargs: Additional LM Studio specific configuration
        """
        super().__init__(model_id, host=host, **kwargs)
        self.host = host
        self.model = None

    def initialize(self) -> bool:
        """Initialize connection to LM Studio."""
        try:
            import lmstudio as lms
            # Create a client with the specified host (without http:// prefix)
            client = lms.Client(api_host=f"{self.host}:1234")
            # Get the LLM using the client
            self.model = client.llm.model(self.model_id)
            logger.info(f"Connected to LMStudio at {self.host} with model: {self.model_id}")
            return True
        except ImportError:
            logger.error("LMStudio package not available. Please install: pip install lmstudio")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to LMStudio at {self.host}: {e}")
            return False

    def act(self, instruction: str, available_actions: Optional[List[Callable]] = None, **kwargs) -> str:
        """Execute instruction using LM Studio model with function calling."""
        if not self.model:
            raise RuntimeError("LM Studio model not initialized. Call initialize() first.")

        try:
            # Use LMStudio's act() function with the model instance
            # This leverages LM Studio's built-in function calling capabilities
            response = self.model.act(
                instruction,
                available_actions or [],
                on_message=kwargs.get('on_message', lambda msg: None)
            )
            return str(response) if response else "No action result received"
        except Exception as e:
            logger.error(f"Error in LM Studio action execution: {e}")
            raise RuntimeError(f"LM Studio action execution failed: {e}")

    def is_available(self) -> bool:
        """Check if LM Studio is available."""
        try:
            import lmstudio
            return self.model is not None
        except ImportError:
            return False


class OllamaProvider(ModelProvider):
    """Ollama model provider implementation."""

    def __init__(self, model_id: str = "llama3.2", host: str = "localhost", port: int = 11434, **kwargs):
        """
        Initialize Ollama provider.

        Args:
            model_id: Ollama model identifier
            host: Ollama server host
            port: Ollama server port
            **kwargs: Additional Ollama specific configuration
        """
        super().__init__(model_id, host=host, port=port, **kwargs)
        self.base_url = f"http://{host}:{port}"

    def initialize(self) -> bool:
        """Initialize connection to Ollama."""
        try:
            import requests
            # Test connection to Ollama server
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                if self.model_id in model_names or any(self.model_id in name for name in model_names):
                    logger.info(f"Connected to Ollama with model: {self.model_id}")
                    return True
                else:
                    logger.error(f"Model {self.model_id} not found in Ollama. Available models: {model_names}")
                    return False
            else:
                logger.error(f"Failed to connect to Ollama at {self.base_url}")
                return False
        except ImportError:
            logger.error("Requests package not available. Please install: pip install requests")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False

    def act(self, instruction: str, available_actions: Optional[List[Callable]] = None, **kwargs) -> str:
        """Execute instruction using Ollama model."""
        try:
            import requests
            import json

            # Build action-oriented prompt
            action_prompt = self._build_action_prompt(instruction, available_actions)

            payload = {
                "model": self.model_id,
                "prompt": action_prompt,
                "stream": False
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # Longer timeout for action execution
            )

            if response.status_code == 200:
                result = response.json()
                action_result = result.get("response", "No action result received")
                return self._process_action_result(action_result, available_actions)
            else:
                raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in Ollama action execution: {e}")
            raise RuntimeError(f"Ollama action execution failed: {e}")

    def _build_action_prompt(self, instruction: str, available_actions: Optional[List[Callable]] = None) -> str:
        """Build an action-oriented prompt for Ollama."""
        prompt = f"""You are an AI agent that executes infrastructure management tasks.

INSTRUCTION: {instruction}

AVAILABLE ACTIONS:"""

        if available_actions:
            for action in available_actions:
                action_name = action.__name__.replace('_', ' ').title()
                doc = action.__doc__ or "No description available"
                prompt += f"\n- {action_name}: {doc.strip()}"

        prompt += """

You must:
1. Analyze the instruction
2. Determine the appropriate action(s) to take
3. Execute the action(s)
4. Return the result

Focus on TAKING ACTION, not just describing what you would do.
Respond with the actual execution result."""

        return prompt

    def _process_action_result(self, result: str, available_actions: Optional[List[Callable]] = None) -> str:
        """Process and enhance the action result from Ollama."""
        # For now, return the result as-is
        # In a more sophisticated implementation, this could parse the result
        # and actually execute the suggested actions
        return result

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class CloudProvider(ModelProvider):
    """Cloud-based model provider (OpenAI, Anthropic, etc.)."""

    def __init__(self, model_id: str, provider_type: str = "openai", api_key: Optional[str] = None, **kwargs):
        """
        Initialize cloud provider.

        Args:
            model_id: Model identifier (e.g., "gpt-4", "claude-3-sonnet")
            provider_type: Type of cloud provider ("openai", "anthropic", etc.)
            api_key: API key for the service
            **kwargs: Additional provider specific configuration
        """
        super().__init__(model_id, provider_type=provider_type, api_key=api_key, **kwargs)
        self.provider_type = provider_type
        self.api_key = api_key
        self.client = None

    def initialize(self) -> bool:
        """Initialize connection to cloud provider."""
        try:
            if self.provider_type == "openai":
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info(f"Connected to OpenAI with model: {self.model_id}")
                return True
            elif self.provider_type == "anthropic":
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info(f"Connected to Anthropic with model: {self.model_id}")
                return True
            else:
                logger.error(f"Unsupported cloud provider: {self.provider_type}")
                return False
        except ImportError as e:
            logger.error(f"Required package not available for {self.provider_type}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to {self.provider_type}: {e}")
            return False

    def act(self, instruction: str, available_actions: Optional[List[Callable]] = None, **kwargs) -> str:
        """Execute instruction using cloud provider."""
        if not self.client:
            raise RuntimeError(f"{self.provider_type} client not initialized. Call initialize() first.")

        try:
            if self.provider_type == "openai":
                return self._act_openai(instruction, available_actions, **kwargs)
            elif self.provider_type == "anthropic":
                return self._act_anthropic(instruction, available_actions, **kwargs)
            else:
                raise RuntimeError(f"Unsupported provider type: {self.provider_type}")
        except Exception as e:
            logger.error(f"Error in {self.provider_type} action execution: {e}")
            raise RuntimeError(f"{self.provider_type} action execution failed: {e}")

    def _act_openai(self, instruction: str, available_actions: Optional[List[Callable]] = None, **kwargs) -> str:
        """Execute instruction using OpenAI with function calling."""
        messages = [
            {
                "role": "system",
                "content": "You are an AI agent that executes infrastructure management tasks. You have access to various actions to manage hosts, containers, and agents. When given an instruction, determine the appropriate action(s) to take and execute them. Focus on taking action, not just describing what you would do."
            },
            {
                "role": "user",
                "content": f"Execute this instruction: {instruction}"
            }
        ]

        # Prepare function calling if available
        tools = None
        if available_actions:
            tools = self._prepare_openai_tools(available_actions)

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None,
            max_tokens=kwargs.get("max_tokens", 1000)
        )

        # Process response and function calls
        return self._process_openai_response(response, available_actions)

    def _act_anthropic(self, instruction: str, available_actions: Optional[List[Callable]] = None, **kwargs) -> str:
        """Execute instruction using Anthropic."""
        # Build action-oriented prompt
        system_prompt = "You are an AI agent that executes infrastructure management tasks. Focus on taking action, not just describing what you would do."

        action_prompt = f"Execute this instruction: {instruction}"

        if available_actions:
            action_prompt += "\n\nAvailable actions:"
            for action in available_actions:
                action_name = action.__name__.replace('_', ' ').title()
                doc = action.__doc__ or "No description available"
                action_prompt += f"\n- {action_name}: {doc.strip()}"

        response = self.client.messages.create(
            model=self.model_id,
            system=system_prompt,
            max_tokens=kwargs.get("max_tokens", 1000),
            messages=[{"role": "user", "content": action_prompt}]
        )
        return response.content[0].text

    def _prepare_openai_tools(self, available_actions: List[Callable]) -> List[Dict]:
        """Prepare OpenAI function calling tools."""
        tools = []
        for action in available_actions:
            tool = {
                "type": "function",
                "function": {
                    "name": action.__name__,
                    "description": action.__doc__ or f"Execute {action.__name__}",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            tools.append(tool)
        return tools

    def _process_openai_response(self, response, available_actions: Optional[List[Callable]] = None) -> str:
        """Process OpenAI response and execute any function calls."""
        message = response.choices[0].message

        if message.tool_calls:
            # Function calls were made - this indicates action execution
            results = []
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                results.append(f"Executed {function_name}")
            return f"Actions executed: {', '.join(results)}. {message.content or ''}"
        else:
            # No function calls - return the message content
            return message.content or "No action result received"

    def is_available(self) -> bool:
        """Check if cloud provider is available."""
        return self.client is not None


def create_model_provider(provider_type: str = "lmstudio", **kwargs) -> ModelProvider:
    """
    Factory function to create model providers.

    Args:
        provider_type: Type of provider ("lmstudio", "ollama", "openai", "anthropic")
        **kwargs: Provider-specific configuration

    Returns:
        Configured model provider instance
    """
    providers = {
        "lmstudio": LMStudioProvider,
        "ollama": OllamaProvider,
        "openai": lambda **kw: CloudProvider(provider_type="openai", **kw),
        "anthropic": lambda **kw: CloudProvider(provider_type="anthropic", **kw),
    }

    if provider_type not in providers:
        raise ValueError(f"Unsupported provider type: {provider_type}. Available: {list(providers.keys())}")

    # Handle parameter mapping for different providers
    if provider_type == "ollama":
        # Map CLI parameters to OllamaProvider parameters
        provider_kwargs = {}
        if "ollama_host" in kwargs:
            provider_kwargs["host"] = kwargs["ollama_host"]
        if "ollama_port" in kwargs:
            provider_kwargs["port"] = kwargs["ollama_port"]

        # Add any other kwargs that don't conflict
        for key, value in kwargs.items():
            if key not in ["ollama_host", "ollama_port"]:
                provider_kwargs[key] = value

        return providers[provider_type](**provider_kwargs)
    else:
        # For other providers, pass kwargs as-is
        return providers[provider_type](**kwargs)