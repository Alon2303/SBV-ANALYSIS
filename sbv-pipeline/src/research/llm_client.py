"""LLM client for OpenAI and Anthropic."""
import json
from typing import Optional, Dict, Any, List
from ..config import settings


class LLMClient:
    """Client for LLM API calls."""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        self.provider = provider or settings.default_llm_provider
        self.model = model or settings.default_model
        self.temperature = temperature or settings.temperature
        self.max_tokens = max_tokens or settings.max_tokens
        
        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=settings.anthropic_api_key)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> str:
        """
        Get completion from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            json_mode: Whether to request JSON output
        
        Returns:
            LLM response text
        """
        if self.provider == "openai":
            return self._complete_openai(prompt, system_prompt, json_mode)
        elif self.provider == "anthropic":
            return self._complete_anthropic(prompt, system_prompt, json_mode)
    
    def _complete_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_mode: bool
    ) -> str:
        """OpenAI completion."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    def _complete_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_mode: bool
    ) -> str:
        """Anthropic completion."""
        if json_mode:
            prompt += "\n\nPlease respond with valid JSON only."
        
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self.client.messages.create(**kwargs)
        return response.content[0].text
    
    def extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from response text."""
        # Try to parse directly
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_text = text[start:end].strip()
            return json.loads(json_text)
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_text = text[start:end].strip()
            return json.loads(json_text)
        
        raise ValueError("Could not extract JSON from response")

