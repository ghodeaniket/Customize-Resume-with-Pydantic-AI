"""Test script for the OpenRouter client."""
import asyncio
import logging
import os
import json
from dotenv import load_dotenv
from infrastructure.openrouter_client import OpenRouterClient


def configure_logging():
    """Configure logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(filename)s:%(lineno)d | %(message)s"
    )
    logging.getLogger("httpx").setLevel(logging.DEBUG)


def mask_api_key(key):
    """Mask the API key for display."""
    if not key:
        return "None"
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


async def test_openrouter_client():
    """Test the OpenRouter client."""
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    configure_logging()
    logger = logging.getLogger("test")
    
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable is not set.")
        return
    
    masked_key = mask_api_key(api_key)
    logger.info(f"Using API key: {masked_key}")
    
    # Test with curl equivalent
    logger.info("Testing equivalent curl command (for reference only):")
    logger.info("curl -X POST https://openrouter.ai/api/v1/chat/completions " + 
                "-H 'Content-Type: application/json' " + 
                "-H 'Authorization: Bearer API_KEY' " + 
                "-d '{\"model\": \"deepseek/deepseek-r1-distill-llama-70b\", " + 
                "\"messages\": [{\"role\": \"user\", \"content\": \"Say hello world!\"}]}'")
    
    logger.info("Testing OpenRouter client...")
    
    # Create client
    client = OpenRouterClient(api_key)
    
    # Create messages for the request
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello world!"}
    ]
    
    # Log the request payload
    payload = {
        "model": "deepseek/deepseek-r1-distill-llama-70b",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 20,
        "stream": False
    }
    logger.info(f"Request payload: {json.dumps(payload)}")
    
    # Log the headers being sent
    headers = {
        "Authorization": f"Bearer {masked_key}",
        "HTTP-Referer": "https://resume-customizer.example.com",
        "X-Title": "Resume Customizer",
        "Content-Type": "application/json"
    }
    logger.info(f"Request headers: {headers}")
    
    try:
        # Make a simple request
        response = await client.chat_completion(
            messages=messages,
            model="deepseek/deepseek-r1-distill-llama-70b",
            temperature=0.7,
            max_tokens=20
        )
        
        # Check response
        if "choices" in response and len(response["choices"]) > 0:
            if "message" in response["choices"][0]:
                content = response["choices"][0]["message"]["content"]
                logger.info(f"Response: {content}")
                logger.info("OpenRouter client test passed!")
            else:
                logger.error("No message in response.")
        else:
            logger.error("No choices in response.")
            
    except Exception as e:
        logger.error(f"OpenRouter client test failed: {str(e)}")
    
    # Close client
    await client.close()


if __name__ == "__main__":
    asyncio.run(test_openrouter_client())
