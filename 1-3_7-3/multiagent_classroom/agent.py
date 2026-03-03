"""
Agent Module

Defines agent classes for classroom simulation with LLM interaction.
"""

import time
import logging
from typing import List, Dict, Optional
from openai import OpenAI
import google.generativeai as genai

from . import constants as const


logger = logging.getLogger(__name__)


class SimpleAgent:
    """
    Agent for COPUS classroom simulation with LLM interaction.
    
    Manages conversation context and generates responses using
    DeepSeek or Google Gemini models.
    
    Attributes:
        name: Agent identifier name
        system_prompt: System instruction defining agent behavior
        model_name: LLM model name
        max_context: Maximum messages to keep in context window
        api_provider: API provider ("deepseek" or "google")
        client: OpenAI client instance (for DeepSeek)
        model: Google Gemini model instance (for Google)
        chat: Google Gemini chat session (for Google)
        messages: Message history (for DeepSeek/OpenAI)
    """
    
    def __init__(
        self, 
        name: str, 
        system_prompt: str, 
        model_name: str,
        api_provider: str,
        client: Optional[OpenAI] = None,
        max_context: int = 10
    ) -> None:
        """
        Initialize agent with configuration.
        
        Args:
            name: Agent identifier name
            system_prompt: System instruction for agent behavior
            model_name: LLM model name to use
            api_provider: API provider ("deepseek" or "google")
            client: OpenAI client instance (required if using DeepSeek)
            max_context: Maximum messages in context window (default: 10)
        """
        self.name: str = name
        self.system_prompt: str = system_prompt
        self.model_name: str = model_name
        self.max_context: int = max_context
        self.api_provider: str = api_provider
        self.client: Optional[OpenAI] = client
        
        if api_provider == "google":
            self.model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
            self.chat = self.model.start_chat(history=[])
        else:
            self.messages: List[Dict[str, str]] = [
                {"role": "system", "content": system_prompt}
            ]
    
    def generate_response(
        self, 
        prompt: str, 
        temperature: float = const.TEMPERATURE, 
        max_tokens: int = const.MAX_TOKENS
    ) -> str:
        """
        Generate response from LLM with retry logic.
        
        Args:
            prompt: User prompt to send to LLM
            temperature: Sampling temperature (default: from constants)
            max_tokens: Maximum tokens in response (default: from constants)
            
        Returns:
            Generated response text or error message if all retries fail
        """
        for attempt in range(const.MAX_RETRIES):
            try:
                if self.api_provider == "google":
                    return self._generate_google_response(prompt)
                else:
                    return self._generate_deepseek_response(prompt, temperature, max_tokens)
            except Exception as e:
                if attempt < const.MAX_RETRIES - 1:
                    self._handle_retry(attempt, e)
                else:
                    return self._handle_max_retries_exceeded(e)
        
        return "[ERROR: Max retries exceeded]"
    
    def _generate_google_response(self, prompt: str) -> str:
        """
        Generate response using Google Gemini API.
        
        Args:
            prompt: User prompt
            
        Returns:
            Generated response text
        """
        response = self.chat.send_message(prompt)
        return response.text.strip()
    
    def _generate_deepseek_response(
        self, 
        prompt: str, 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """
        Generate response using DeepSeek/OpenAI API.
        
        Manages conversation history and applies sliding window
        context management.
        
        Args:
            prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response text
        """
        self.messages.append({"role": "user", "content": prompt})
        self._apply_context_window()
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        answer: str = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": answer})
        return answer
    
    def _apply_context_window(self) -> None:
        """
        Apply sliding window to maintain context size limit.
        
        Keeps system message and most recent messages within max_context limit.
        """
        if len(self.messages) > (self.max_context + 1):
            system_msg: Dict[str, str] = self.messages[0]
            recent: List[Dict[str, str]] = self.messages[-(self.max_context):]
            self.messages = [system_msg] + recent
    
    def _handle_retry(self, attempt: int, error: Exception) -> None:
        """
        Handle retry with exponential backoff.
        
        Args:
            attempt: Current retry attempt number (0-indexed)
            error: Exception that triggered the retry
        """
        wait_time: int = 2 ** attempt
        logger.warning(f"{self.name} - Retry {attempt+1} after {wait_time}s...")
        time.sleep(wait_time)
    
    def _handle_max_retries_exceeded(self, error: Exception) -> str:
        """
        Handle case when max retries exceeded.
        
        Args:
            error: Final exception that occurred
            
        Returns:
            Error message string
        """
        error_msg = f"[ERROR: {str(error)}]"
        logger.error(f"{self.name} - Max retries exceeded: {str(error)}")
        return error_msg
    
    def get_context_size(self) -> int:
        """
        Get current context size.
        
        Returns:
            Number of messages in context (for DeepSeek) or 0 (for Google)
        """
        if self.api_provider == "google":
            return 0  # Google manages history internally
        return len(self.messages)
    
    def clear_context(self) -> None:
        """Clear conversation history while preserving system prompt."""
        if self.api_provider == "google":
            self.chat = self.model.start_chat(history=[])
        else:
            self.messages = [{"role": "system", "content": self.system_prompt}]
