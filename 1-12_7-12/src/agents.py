"""
Agent classes for SimClass Multi-Agent Simulation
Includes SimAgent base class and SimulatedUser specialized class
"""

import random
import time
from openai import OpenAI
import google.generativeai as genai

# Global variables set by main script
API_PROVIDER = None
client = None


class SimAgent:
    """Base agent class with sliding window context management."""
    
    def __init__(self, name, system_prompt, model_name, max_context_window=None):
        self.name = name
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.max_context_window = max_context_window  # None = unlimited (for Summary Seeker)
        
        # Initialize based on API provider
        if API_PROVIDER == "google":
            self.model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
            self.chat = self.model.start_chat(history=[])
        else:  # deepseek
            # For DeepSeek: include system prompt ONCE at initialization
            self.messages = [
                {"role": "system", "content": system_prompt}
            ]

    def reset_context(self):
        """Reset chat history for a new session."""
        if API_PROVIDER == "google":
            self.chat = self.model.start_chat(history=[])
        else:  # deepseek
            # Reset but keep system prompt
            self.messages = [
                {"role": "system", "content": self.system_prompt}
            ]

    def generate_response(self, prompt_text, temperature=0.7, max_tokens=2000, 
                         max_retries=5, initial_delay=1):
        """Send prompt to Agent to get a response with retry logic."""
        
        for attempt in range(max_retries):
            try:
                if API_PROVIDER == "google":
                    # Google Gemini API
                    response = self.chat.send_message(prompt_text)
                    return response.text.strip()
                else:
                    # DeepSeek API (OpenAI-compatible)
                    self.messages.append({"role": "user", "content": prompt_text})
                    
                    # Apply sliding window if max_context_window is set
                    if self.max_context_window is not None and len(self.messages) > (self.max_context_window + 1):
                        # Keep system prompt + last N messages
                        system_prompt_msg = self.messages[0]
                        recent_messages = self.messages[-(self.max_context_window):]
                        self.messages = [system_prompt_msg] + recent_messages
                    
                    # Send all messages (system prompt already in self.messages[0])
                    response = client.chat.completions.create(
                        model=self.model_name,
                        messages=self.messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    assistant_message = response.choices[0].message.content.strip()
                    self.messages.append({"role": "assistant", "content": assistant_message})
                    return assistant_message
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"  [API Error] {self.name} - Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    print(f"  [FATAL] {self.name} - All retries exhausted: {e}")
                    return f"[ERROR: {e}]"
                    
        return "[ERROR: Failed to generate response after retries]"


class SimulatedUser(SimAgent):
    """Represents a real shy student learning ML for the first time."""
    
    def __init__(self, name, system_prompt, model_name, max_context_window=None):
        super().__init__(name, system_prompt, model_name, max_context_window)
        self.confusion_level = 0.0
        self.courage_level = 0.0
        self.fear_level = 0.9
        self.understanding_level = 0.0
        self.questions_asked_count = 0
    
    def reset_context(self):
        """Reset chat history and psychological state for a new session."""
        super().reset_context()
        self.confusion_level = 0.0
        self.courage_level = 0.0
        self.fear_level = 0.9
        self.understanding_level = 0.0
        self.questions_asked_count = 0
    
    def update_confusion(self, slide_difficulty, lecture_complexity):
        """Update confusion level based on lecture complexity."""
        base_confusion = slide_difficulty * 0.3
        
        if lecture_complexity > 300:  # Long lecture
            base_confusion += 0.2
        
        self.confusion_level = min(1.0, base_confusion)
        self.understanding_level = max(0.0, self.understanding_level - base_confusion * 0.5)
    
    def update_courage(self, peer_name, question_complexity):
        """Update courage based on peer questions."""
        courage_boost = 0
        
        if peer_name == "Curious Baby":
            courage_boost = 0.15
        elif peer_name == "Mr. Clown":
            courage_boost = 0.10
        elif peer_name == "Deep Thinker":
            if question_complexity == "advanced":
                courage_boost = 0.03
                self.fear_level = min(1.0, self.fear_level + 0.15)
            else:
                courage_boost = 0.07
        elif peer_name == "Summary Seeker":
            courage_boost = 0.03
        
        self.courage_level = min(1.0, self.courage_level + courage_boost)
        self.fear_level = max(0.0, self.fear_level - courage_boost * 0.5)
    
    def apply_teacher_encouragement(self):
        """Teacher directly invites student to speak."""
        self.courage_level = min(1.0, self.courage_level + 0.30)
        self.fear_level = max(0.0, self.fear_level - 0.25)
    
    def apply_positive_response(self):
        """After asking and receiving warm response."""
        self.courage_level = min(1.0, self.courage_level + 0.40)
        self.fear_level = max(0.0, self.fear_level - 0.30)
        self.questions_asked_count += 1
    
    def should_speak(self):
        """Decide whether to speak based on internal state."""
        confusion_threshold = 0.7
        courage_threshold = 0.5
        
        is_confused_enough = self.confusion_level > confusion_threshold
        has_enough_courage = self.courage_level > courage_threshold
        
        if is_confused_enough and has_enough_courage:
            speak_probability = (
                self.confusion_level * 0.4 +
                self.courage_level * 0.4 -
                self.fear_level * 0.5
            )
            return random.random() < speak_probability
        
        return False
    
    def should_give_passive_response(self):
        """Decide whether to give a passive (Code 8) vs active (Code 9) response."""
        passive_probability = (
            self.fear_level * 0.7 +
            (1.0 - self.courage_level) * 0.5
        )
        return random.random() < max(0.70, min(0.85, passive_probability))
    
    def generate_response(self, prompt_text, **kwargs):
        """Override to inject current state into prompt."""
        state_info = (f"\n[Your current internal state: understanding={self.understanding_level:.2f}, "
                     f"confusion={self.confusion_level:.2f}, courage={self.courage_level:.2f}, "
                     f"fear={self.fear_level:.2f}]")
        enhanced_prompt = prompt_text + state_info
        return super().generate_response(enhanced_prompt, **kwargs)
