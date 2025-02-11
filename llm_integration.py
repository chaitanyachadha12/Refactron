"""
Author: Chaitanya Chadha
Email: chaitanyachadha12@gmail.com
"""

import requests
import json

class LLMIntegration:
    """
    Handles communication with the local LLM (e.g., Ollama running deepseek-r1:8b).

    IMPORTANT:
    - Ensure your local LLM server is running.
    """

    def __init__(self, api_url: str = "http://localhost:11434", generate_endpoint: str = "/api/generate"):
        self.api_url = api_url
        self.generate_endpoint = generate_endpoint
        print("Warning: No health endpoint available. Skipping health check.")

    def send_prompt(self, prompt: str) -> str:
        """
        Send a prompt to the LLM and return its aggregated response.
        If the response contains multiple JSON objects (one per line),
        this method will concatenate the "response" values from all objects.
        
        :param prompt: The prompt string to send.
        :return: A single aggregated response string from the LLM,
                 or an empty string if parsing fails.
        """
        try:
            payload = {"prompt": prompt, "model": "deepseek-r1:8b"}
            response = requests.post(self.api_url + self.generate_endpoint, json=payload, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors.
            try:
                # First, try to parse the entire response as a single JSON object.
                data = response.json()
                return data.get("response", "")
            except json.JSONDecodeError:
                # If that fails, try to parse the response line by line.
                raw_text = response.text.strip()
                lines = raw_text.splitlines()
                accumulated_response = ""
                for line in lines:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            accumulated_response += data.get("response", "")
                    except json.JSONDecodeError:
                        continue
                if accumulated_response:
                    return accumulated_response.strip()
                else:
                    print("Error: Unable to parse response as JSON.")
                    return ""
        except requests.exceptions.Timeout:
            print("Error: Request to LLM timed out.")
            return ""
        except requests.exceptions.RequestException as e:
            print(f"Error: Request to LLM failed: {e}")
            return ""
