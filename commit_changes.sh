#!/bin/bash
# Script to commit all changes to the Resume Customizer project

# Add all changes
git add .

# Create the commit with a detailed message
git commit -m "Fix server configuration and endpoint issues

This commit includes several important fixes:

1. API Endpoint Fixes:
   - Fixed response validation in FastAPI endpoints
   - Updated the endpoints to return CustomizationResponse directly
   - Improved error handling in file processing endpoints

2. Agent Fixes:
   - Added missing LoggerMixin import in strategist.py
   - Fixed ResearcherAgent to properly handle job descriptions as text
   - Ensured fallback prompts work correctly when templates aren't found

3. Environment Configuration:
   - Simplified and standardized environment variables
   - Fixed inconsistencies in configuration naming
   - Created cleaner .env file with only essential variables

4. Server Setup:
   - Added proper server setup and documentation
   - Created comprehensive testing tools for file processing
   - Added detailed API documentation

Known Issues:
- Missing prompt templates (warnings in logs, but fallback prompts are working)
- Some paths may need adjustment depending on the deployment environment
- File processing might need further refinement for complex documents

Testing completed:
- Server startup successful
- File upload and processing working
- Resume customization with job description text verified
"

echo "Changes committed successfully."
echo "You can push these changes to your repository with: git push"
