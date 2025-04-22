"""Command-line interface for the Resume Customizer application.

This module provides a command-line interface for running the application
and performing administrative tasks.
"""

import argparse
import asyncio
import os
import sys
from typing import Any, Dict, List, Optional

import httpx
import uvicorn

from resume_customizer import __version__
from resume_customizer.agents.profiler import analyze_resume
from resume_customizer.agents.researcher import analyze_job_description
from resume_customizer.agents.strategist import customize_resume
from resume_customizer.core.config import settings
from resume_customizer.core.logging import app_logger as logger, setup_logging


def setup_parser() -> argparse.ArgumentParser:
    """Set up the command-line argument parser.
    
    Returns:
        ArgumentParser: The argument parser
    """
    parser = argparse.ArgumentParser(
        description=f"Resume Customizer CLI v{__version__}",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Global arguments
    parser.add_argument(
        "--version", "-v", action="version", 
        version=f"Resume Customizer v{__version__}"
    )
    parser.add_argument(
        "--log-level", type=str, default=settings.LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )
    
    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Run the API server")
    serve_parser.add_argument(
        "--host", type=str, default="127.0.0.1",
        help="Host to bind the server to"
    )
    serve_parser.add_argument(
        "--port", type=int, default=8000,
        help="Port to bind the server to"
    )
    serve_parser.add_argument(
        "--reload", action="store_true", 
        help="Enable auto-reload on code changes"
    )
    
    # Analyze resume command
    analyze_resume_parser = subparsers.add_parser(
        "analyze-resume", help="Analyze a resume file"
    )
    analyze_resume_parser.add_argument(
        "resume_file", type=str, help="Path to the resume file"
    )
    analyze_resume_parser.add_argument(
        "--model", type=str, default=None,
        help="Model to use for analysis"
    )
    analyze_resume_parser.add_argument(
        "--output", type=str, default=None,
        help="Output file to write the analysis to (default: stdout)"
    )
    
    # Analyze job description command
    analyze_job_parser = subparsers.add_parser(
        "analyze-job", help="Analyze a job description file"
    )
    analyze_job_parser.add_argument(
        "job_file", type=str, help="Path to the job description file"
    )
    analyze_job_parser.add_argument(
        "--model", type=str, default=None,
        help="Model to use for analysis"
    )
    analyze_job_parser.add_argument(
        "--output", type=str, default=None,
        help="Output file to write the analysis to (default: stdout)"
    )
    
    # Customize resume command
    customize_parser = subparsers.add_parser(
        "customize", help="Customize a resume for a job"
    )
    customize_parser.add_argument(
        "resume_file", type=str, help="Path to the resume file"
    )
    customize_parser.add_argument(
        "job_file", type=str, help="Path to the job description file"
    )
    customize_parser.add_argument(
        "--model", type=str, default=None,
        help="Model to use for customization"
    )
    customize_parser.add_argument(
        "--output", type=str, default=None,
        help="Output file to write the customized resume to (default: stdout)"
    )
    
    return parser


def serve_command(args: argparse.Namespace) -> None:
    """Run the API server.
    
    Args:
        args: Command-line arguments
    """
    logger.info(f"Starting API server on {args.host}:{args.port}")
    uvicorn.run(
        "resume_customizer.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower()
    )


async def analyze_resume_command(args: argparse.Namespace) -> None:
    """Analyze a resume file.
    
    Args:
        args: Command-line arguments
    """
    logger.info(f"Analyzing resume file: {args.resume_file}")
    
    try:
        # Read the resume file
        with open(args.resume_file, "r", encoding="utf-8") as f:
            resume_content = f.read()
        
        # Analyze the resume
        async with httpx.AsyncClient() as client:
            profile = await analyze_resume(
                resume_content=resume_content,
                http_client=client,
                model_name=args.model
            )
        
        # Format the profile as JSON
        import json
        profile_json = json.dumps(profile.dict(), indent=2)
        
        # Output the profile
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(profile_json)
            logger.info(f"Analysis written to {args.output}")
        else:
            print(profile_json)
        
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        sys.exit(1)


async def analyze_job_command(args: argparse.Namespace) -> None:
    """Analyze a job description file.
    
    Args:
        args: Command-line arguments
    """
    logger.info(f"Analyzing job description file: {args.job_file}")
    
    try:
        # Read the job description file
        with open(args.job_file, "r", encoding="utf-8") as f:
            job_content = f.read()
        
        # Analyze the job description
        async with httpx.AsyncClient() as client:
            requirements = await analyze_job_description(
                job_description=job_content,
                http_client=client,
                model_name=args.model
            )
        
        # Format the requirements as JSON
        import json
        requirements_json = json.dumps(requirements.dict(), indent=2)
        
        # Output the requirements
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(requirements_json)
            logger.info(f"Analysis written to {args.output}")
        else:
            print(requirements_json)
        
    except Exception as e:
        logger.error(f"Error analyzing job description: {str(e)}")
        sys.exit(1)


async def customize_command(args: argparse.Namespace) -> None:
    """Customize a resume for a job.
    
    Args:
        args: Command-line arguments
    """
    logger.info(f"Customizing resume file: {args.resume_file}")
    logger.info(f"For job description file: {args.job_file}")
    
    try:
        # Read the resume file
        with open(args.resume_file, "r", encoding="utf-8") as f:
            resume_content = f.read()
        
        # Read the job description file
        with open(args.job_file, "r", encoding="utf-8") as f:
            job_content = f.read()
        
        # Customize the resume
        async with httpx.AsyncClient() as client:
            optimized_resume = await customize_resume(
                resume_content=resume_content,
                job_description=job_content,
                http_client=client,
                model_name=args.model
            )
        
        # Format the optimized resume as JSON
        import json
        resume_json = json.dumps(optimized_resume.dict(), indent=2)
        resume_content = optimized_resume.content
        
        # Output the optimized resume
        if args.output:
            # Determine if we should output JSON or markdown
            if args.output.endswith(".json"):
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(resume_json)
            else:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(resume_content)
            logger.info(f"Customized resume written to {args.output}")
        else:
            print(resume_content)
        
    except Exception as e:
        logger.error(f"Error customizing resume: {str(e)}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    parser = setup_parser()
    args = parser.parse_args()
    
    # Configure logging
    setup_logging(args.log_level)
    
    # If no command is specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run the appropriate command
    if args.command == "serve":
        serve_command(args)
    elif args.command == "analyze-resume":
        asyncio.run(analyze_resume_command(args))
    elif args.command == "analyze-job":
        asyncio.run(analyze_job_command(args))
    elif args.command == "customize":
        asyncio.run(customize_command(args))


if __name__ == "__main__":
    main()
