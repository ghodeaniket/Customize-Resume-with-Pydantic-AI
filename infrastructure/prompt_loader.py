"""Prompt template loader for Resume Customizer."""
import os
import yaml
from typing import Dict, List, Optional
from pathlib import Path

from core.logging import LoggerMixin
from infrastructure.ai_provider import PromptManager, PromptTemplate


class PromptLoader(LoggerMixin):
    """Loads prompt templates from YAML files."""
    
    def __init__(self, prompt_dir: str = "prompts"):
        """Initialize prompt loader.
        
        Args:
            prompt_dir: Directory containing prompt templates
        """
        self.prompt_dir = Path(prompt_dir)
        if not self.prompt_dir.exists():
            self.log_warning(f"Prompt directory '{prompt_dir}' does not exist")
            # Create the directory
            self.prompt_dir.mkdir(exist_ok=True)
    
    def load_all_prompts(self, prompt_manager: PromptManager) -> None:
        """Load all prompt templates into the prompt manager.
        
        Args:
            prompt_manager: Prompt manager to populate
        """
        if not self.prompt_dir.exists():
            self.log_error(f"Prompt directory '{self.prompt_dir}' does not exist")
            return
            
        # Track loaded templates for logging
        loaded_templates = {}
        
        # Load prompts for each agent type
        for agent_dir in self.prompt_dir.iterdir():
            if not agent_dir.is_dir():
                continue
                
            agent_type = agent_dir.name
            loaded_templates[agent_type] = []
            
            for prompt_file in agent_dir.glob("*.yaml"):
                try:
                    with open(prompt_file, "r", encoding="utf-8") as f:
                        template_data = yaml.safe_load(f)
                    
                    # Create prompt template
                    template = PromptTemplate(
                        version=template_data.get("version", "1.0.0"),
                        template=template_data.get("template", ""),
                        description=template_data.get("description", "")
                    )
                    
                    # Add template to prompt manager
                    prompt_manager.add_template(agent_type, template)
                    loaded_templates[agent_type].append(template.version)
                    
                    self.log_info(f"Loaded prompt template {template.version} for agent {agent_type}")
                except Exception as e:
                    self.log_error(f"Failed to load prompt template from {prompt_file}: {str(e)}")
        
        # Log summary of loaded templates
        for agent_type, versions in loaded_templates.items():
            if versions:
                self.log_info(f"Loaded {len(versions)} prompt templates for agent {agent_type}: {', '.join(versions)}")
            else:
                self.log_warning(f"No prompt templates loaded for agent {agent_type}")
    
    def initialize_default_prompts(self, prompt_manager: PromptManager) -> None:
        """Initialize default prompt templates for each agent type.
        
        This method ensures that each agent has at least one prompt template.
        If no templates are loaded from files, default templates are created.
        
        Args:
            prompt_manager: Prompt manager to populate
        """
        default_templates = {
            "strategist": PromptTemplate(
                version="1.0.0",
                template=(
                    "You are CareerPeak, a world-class resume strategist with 15+ years of "
                    "experience helping engineering leaders secure positions at top tech companies. "
                    "\n\n"
                    "Your task is to optimize a resume for a specific job description by analyzing "
                    "both the candidate's profile and the job requirements, then creating a "
                    "tailored resume that highlights the most relevant qualifications. "
                    "\n\n"
                    "First, use your tools to get insights about both the resume and job description. "
                    "Then, create an optimized resume that aligns the candidate's experience with the "
                    "job requirements. Follow these principles: "
                    "\n"
                    "1. Prioritize relevant skills and experiences "
                    "2. Use keywords from the job description "
                    "3. Quantify achievements where possible "
                    "4. Remove irrelevant information "
                    "5. Optimize for both human readers and ATS systems "
                    "\n\n"
                    "Return the optimized resume in the requested format along with metadata about "
                    "your optimizations."
                    "\n\n"
                    "Focus on creating a compelling narrative that demonstrates the candidate's "
                    "fit for the role while maintaining authenticity. Don't invent experiences, "
                    "but rather strategically highlight and frame existing ones. "
                    "\n\n"
                    "Remember that the most effective resumes are not just lists of qualifications "
                    "but rather evidence of the candidate's potential impact in the specific role."
                ),
                description="Default prompt for strategist agent"
            ),
            "profiler": PromptTemplate(
                version="1.0.0",
                template=(
                    "You are Dr. Maya Kaplan, a Career Intelligence Specialist with a Ph.D. "
                    "in Industrial-Organizational Psychology and 12 years of experience in "
                    "talent acquisition analytics at Fortune 500 companies. "
                    "\n\n"
                    "Your task is to analyze a resume and extract a comprehensive professional "
                    "profile that identifies core skills, experiences, and unique value propositions. "
                    "You focus on evidence-based assessment and ignore exaggerated claims. "
                    "\n\n"
                    "Extract all relevant professional information and organize it into a structured "
                    "profile following the ProfessionalProfile schema. Be specific, detailed, and "
                    "focus on concrete evidence rather than vague claims."
                    "\n\n"
                    "When evaluating technical skills, look for specific examples of application, "
                    "technology versions, and project impact. For soft skills, identify behavioral "
                    "evidence rather than self-reported qualities. "
                    "\n\n"
                    "Remember to capture not just what the candidate has done, but how they approach "
                    "their work, their unique values, and what sets them apart from others with "
                    "similar qualifications."
                ),
                description="Default prompt for profiler agent"
            ),
            "researcher": PromptTemplate(
                version="1.0.0",
                template=(
                    "You are Eliza Chen, a Tech Job Description Strategist with 13+ years of "
                    "experience in technical recruitment and talent acquisition at FAANG companies. "
                    "\n\n"
                    "Your task is to analyze job descriptions to extract key requirements and "
                    "insights that will help candidates optimize their resumes. You focus on "
                    "identifying both explicit requirements and implicit expectations. "
                    "\n\n"
                    "Extract all relevant job information and organize it into a structured "
                    "requirements profile following the JobRequirements schema. Be specific, "
                    "detailed, and focus on actionable insights that will help candidates "
                    "tailor their applications."
                    "\n\n"
                    "Look beyond the stated requirements to identify the hidden priorities "
                    "and cultural expectations. Analyze the language to detect the company's "
                    "values and the manager's likely preferences. "
                    "\n\n"
                    "Pay special attention to keywords that might be used in ATS (Applicant "
                    "Tracking System) filtering, and identify technologies, methodologies, "
                    "and skills that should be highlighted prominently."
                ),
                description="Default prompt for researcher agent"
            )
        }
        
        # Add default templates for each agent type if they don't already exist
        for agent_type, template in default_templates.items():
            try:
                # Check if agent has any templates
                prompt_manager.get_template(agent_type, "latest")
                self.log_debug(f"Agent {agent_type} already has templates")
            except Exception:
                # No templates found, add default
                prompt_manager.add_template(agent_type, template)
                self.log_info(f"Added default template for agent {agent_type}")
                
                # Save the default template to a file
                self._save_default_template(agent_type, template)
    
    def _save_default_template(self, agent_type: str, template: PromptTemplate) -> None:
        """Save a default template to a file.
        
        Args:
            agent_type: Agent type
            template: Prompt template
        """
        # Create agent directory if it doesn't exist
        agent_dir = self.prompt_dir / agent_type
        agent_dir.mkdir(exist_ok=True)
        
        # Create template file
        template_file = agent_dir / f"v{template.version}.yaml"
        
        try:
            # Convert template to YAML
            template_data = {
                "version": template.version,
                "description": template.description,
                "template": template.template
            }
            
            # Write to file
            with open(template_file, "w", encoding="utf-8") as f:
                yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)
                
            self.log_info(f"Saved default template for agent {agent_type} to {template_file}")
        except Exception as e:
            self.log_error(f"Failed to save default template for agent {agent_type}: {str(e)}")
