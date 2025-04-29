# Security Best Practices

## API Key Management

### Never commit API keys to the repository

- Always use environment variables for API keys
- Store API keys in `.env` files that are excluded from git (already in `.gitignore`)
- Never log API keys, even partially

### Environment Variables

All sensitive data should be stored in environment variables:

```
# .env file example (DO NOT COMMIT THIS FILE)
OPENROUTER_API_KEY=your-api-key-here
```

### Loading Environment Variables

Use the existing configuration system to load environment variables:

```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openrouter_api_key: str = ""
    
    class Config:
        env_file = ".env"
```

### Testing with API Keys

- Never print or log API keys in tests
- Use masking functions if needed: `mask_key("sk-abcdefg") -> "sk-...efg"`
- Consider using environment variable mocking for tests

### Secure Logging

- Always sanitize logs to remove sensitive information
- Use a masking function for API keys: `mask_key(api_key)`
- Never log full API keys, even in debug logs

## Security Checklist

When committing code, verify:

- [ ] No API keys in the code
- [ ] No API keys in logs or print statements
- [ ] No API keys in test files
- [ ] Environment variables properly used
- [ ] `.env` file not committed
- [ ] No sensitive information in commit messages

## Rotate Compromised Keys

If you suspect an API key has been compromised:

1. Immediately rotate/regenerate the key
2. Check repository history for the exposure
3. Consider using `git filter-branch` to remove the key from history
   (consult with your version control administrator)

## Additional Resources

- [Git Secret Management Best Practices](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Environment Variables in Python](https://docs.python.org/3/library/os.html#os.environ)
- [Python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
