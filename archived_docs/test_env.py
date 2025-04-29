"""Test script for environment variables."""
import os
from dotenv import load_dotenv


def mask_api_key(key):
    """Mask the API key for display."""
    if not key:
        return "None"
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def test_env():
    """Test the environment variables."""
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    masked_key = mask_api_key(api_key)
    
    print(f"OPENROUTER_API_KEY: {masked_key}")
    print(f"Length: {len(api_key) if api_key else 0}")
    
    # Check if API key starts with expected prefix
    if api_key and api_key.startswith("sk-or-v1-"):
        print("API key has correct prefix")
    else:
        print("API key doesn't have expected prefix")


if __name__ == "__main__":
    test_env()
