"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gwu.edu
Created on: 02-06-2025
Updated on: 
"""

import requests
import json

class LLMIntegration:
    """
    LLMIntegration class to handle communication with the local LLM (Ollama using qwen2.5-coder).
    """

    def __init__(self, api_url: str = "http://localhost:11434"):
        """
        Initialize the integration with the default API URL.
        :param api_url: The URL of the local LLM API.
        """
        self.api_url = api_url

    def send_prompt(self, prompt: str) -> str:
        """
        Send a prompt to the LLM and return the response.
        :param prompt: The prompt string to send.
        :return: The response from the LLM, or an empty string in case of an error.
        """
        try:
            # Prepare the payload for the LLM request.
            payload = {"prompt": prompt, "model": "qwen2.5-coder"}
            # Send the prompt to the LLM API.
            response = requests.post(self.api_url + "/generate", json=payload, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad status codes.
            data = response.json()
            return data.get("response", "")
        except requests.exceptions.Timeout:
            print("Error: Request to LLM timed out.")
            return ""
        except requests.exceptions.RequestException as e:
            print(f"Error: Request to LLM failed: {e}")
            return ""
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON response from LLM.")
            return ""
