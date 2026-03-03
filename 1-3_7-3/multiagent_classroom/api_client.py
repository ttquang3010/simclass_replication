"""
API Client Management Module

Handles API initialization and client configuration for DeepSeek and Google Gemini.
"""

import os
import logging
from typing import Optional, Tuple
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv

from . import constants as const


logger = logging.getLogger(__name__)


class APIClient:
    """
    Manages API client initialization and configuration.
    
    Attributes:
        provider: API provider name ("deepseek" or "google")
        client: OpenAI client instance (for DeepSeek)
        model_name: Name of the model being used
    """
    
    def __init__(self) -> None:
        """Initialize APIClient with no configuration."""
        self.provider: Optional[str] = None
        self.client: Optional[OpenAI] = None
        self.model_name: str = ""
    
    def initialize(self) -> Tuple[str, Optional[OpenAI], str]:
        """
        Initialize API client based on available API keys.
        
        Checks for DeepSeek API key first, then Google Gemini API key.
        Configures the appropriate API provider.
        
        Returns:
            Tuple containing:
                - provider: API provider name ("deepseek" or "google")
                - client: OpenAI client instance (None for Google)
                - model_name: Model name being used
                
        Raises:
            Exception: If no valid API key is found in .env file
        """
        load_dotenv()
        
        deepseek_key: Optional[str] = os.getenv("DEEPSEEK_API_KEY", None)
        google_key: Optional[str] = os.getenv("GOOGLE_API_KEY", None)
        
        if deepseek_key:
            self.provider = "deepseek"
            self.client = OpenAI(
                api_key=deepseek_key,
                base_url=const.DEEPSEEK_BASE_URL
            )
            self.model_name = const.DEEPSEEK_MODEL
            logger.info(f"Using DeepSeek API: {self.model_name}")
        elif google_key:
            self.provider = "google"
            genai.configure(api_key=google_key)
            self.model_name = const.GOOGLE_MODEL
            logger.info(f"Using Google Gemini API: {self.model_name}")
        else:
            error_msg = "No API key found in .env file"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        return self.provider, self.client, self.model_name
    
    def get_provider(self) -> Optional[str]:
        """
        Get current API provider.
        
        Returns:
            API provider name or None if not initialized
        """
        return self.provider
    
    def get_client(self) -> Optional[OpenAI]:
        """
        Get OpenAI client instance.
        
        Returns:
            OpenAI client or None if using Google or not initialized
        """
        return self.client
    
    def get_model_name(self) -> str:
        """
        Get current model name.
        
        Returns:
            Model name string
        """
        return self.model_name
