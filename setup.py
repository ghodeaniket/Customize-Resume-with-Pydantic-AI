"""Setup script for the Resume Customizer package."""

from setuptools import find_packages, setup

import resume_customizer


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="resume-customizer",
    version=resume_customizer.__version__,
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered resume customization service using Pydantic AI's multi-agent capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/resume-customizer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "resume-customizer=resume_customizer.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
