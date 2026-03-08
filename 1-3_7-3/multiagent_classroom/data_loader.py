"""
Data Loader Module

Handles loading and validation of prompts and slides data.
"""

import json
import logging
import importlib
from typing import Dict, List, Any

from . import constants as const


logger = logging.getLogger(__name__)


class DataLoader:
    """
    Loads and manages simulation data including prompts and slides.
    """
    
    def __init__(self) -> None:
        """Initialize data loader."""
        self.prompts: Dict[str, Any] = {}
        self.slides: List[Dict[str, Any]] = []
    
    def load_prompts(self, module_name: str = const.AGENT_PROMPTS_MODULE) -> Dict[str, Any]:
        """
        Load agent prompts from Python module.
        
        Args:
            module_name: Python module path (e.g., 'data.agent_prompts_vi')
            
        Returns:
            Dictionary of agent prompts
            
        Raises:
            ImportError: If module cannot be imported
            AttributeError: If module doesn't have required attributes
        """
        try:
            # Import the prompts module dynamically
            prompts_module = importlib.import_module(module_name)
            
            # Get all agent configurations
            self.prompts = prompts_module.get_all_agents()
            
            logger.info(f"Loaded prompts from Python module: {module_name}")
            self._validate_prompts()
            return self.prompts
            
        except ImportError as e:
            logger.error(f"Failed to import prompts module '{module_name}': {e}")
            raise
        except AttributeError as e:
            logger.error(f"Prompts module missing required function 'get_all_agents()': {e}")
            raise
    
    def load_slides(
        self, 
        file_path: str = const.SLIDES_DATA_PATH,
        max_slides: int = None
    ) -> List[Dict[str, Any]]:
        """
        Load slides data from JSON file.
        
        Args:
            file_path: Path to slides JSON file
            max_slides: Maximum number of slides to load (None = load all)
            
        Returns:
            List of slide dictionaries
            
        Raises:
            FileNotFoundError: If slides file not found
            json.JSONDecodeError: If JSON is invalid
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                slides_data: Dict[str, Any] = json.load(f)
            
            self.slides = slides_data["slides"] if max_slides is None else slides_data["slides"][:max_slides]
            
            logger.info(f"Loaded {len(self.slides)} slides from {file_path}")
            self._validate_slides()
            return self.slides
            
        except FileNotFoundError:
            logger.error(f"Slides file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in slides file: {e}")
            raise
        except KeyError as e:
            logger.error(f"Missing 'slides' key in slides data: {e}")
            raise
    
    def load_all(self) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Load both prompts and slides.
        
        Returns:
            Tuple of (prompts, slides)
        """
        prompts: Dict[str, Any] = self.load_prompts()
        slides: List[Dict[str, Any]] = self.load_slides()
        return prompts, slides
    
    def _validate_prompts(self) -> None:
        """
        Validate that prompts contain required keys.
        
        Raises:
            ValueError: If required keys are missing
        """
        required_agents: List[str] = ["teacher", "student_active", "student_passive"]
        
        for agent in required_agents:
            if agent not in self.prompts:
                error_msg = f"Missing required agent: {agent}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if "system_prompt" not in self.prompts[agent]:
                error_msg = f"Missing system_prompt for agent: {agent}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        logger.debug("Prompts validation passed")
    
    def _validate_slides(self) -> None:
        """
        Validate that slides contain required fields.
        
        Raises:
            ValueError: If required fields are missing
        """
        required_fields: List[str] = ["title", "content"]
        
        for i, slide in enumerate(self.slides):
            for field in required_fields:
                if field not in slide:
                    error_msg = f"Slide {i} missing required field: {field}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
        
        logger.debug("Slides validation passed")
    
    def get_prompt(self, agent_name: str) -> Dict[str, Any]:
        """
        Get prompt for specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent prompt dictionary
            
        Raises:
            KeyError: If agent not found
        """
        if agent_name not in self.prompts:
            error_msg = f"Agent not found: {agent_name}"
            logger.error(error_msg)
            raise KeyError(error_msg)
        
        return self.prompts[agent_name]
    
    def get_slide(self, index: int) -> Dict[str, Any]:
        """
        Get slide by index.
        
        Args:
            index: Slide index
            
        Returns:
            Slide dictionary
            
        Raises:
            IndexError: If index out of range
        """
        if index < 0 or index >= len(self.slides):
            error_msg = f"Slide index out of range: {index}"
            logger.error(error_msg)
            raise IndexError(error_msg)
        
        return self.slides[index]
    
    def get_slides_count(self) -> int:
        """
        Get number of loaded slides.
        
        Returns:
            Number of slides
        """
        return len(self.slides)
