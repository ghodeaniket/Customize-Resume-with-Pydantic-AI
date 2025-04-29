# Resume Customizer Architecture Documentation

This directory contains the architectural diagrams and documentation for the Resume Customizer application. These diagrams provide a comprehensive overview of the system's architecture, component relationships, and interaction flows.

## Diagrams

### Architecture Diagram
`architecture-diagram.mermaid` - This diagram shows the overall system architecture with its layers and components:

- API Layer (FastAPI endpoints and middleware)
- Service Layer (ResumeCustomizerService)
- Agent Layer (Strategist, Profiler, Researcher)
- Infrastructure Layer (Document processor, AI provider, etc.)
- Core Layer (Configuration, logging, exceptions)

### Sequence Diagram
`sequence-diagram.mermaid` - This diagram illustrates the sequence of interactions when processing a resume customization request:

- API request handling
- File processing
- Agent interactions
- LLM API calls
- Response generation

### Deployment Diagram
`deployment-diagram.mermaid` - This diagram shows how the application would be deployed in a production environment:

- Load balancing
- Kubernetes cluster
- API services
- Background workers
- Supporting services (monitoring, logging)
- External services (OpenRouter API)

## Viewing Diagrams

These diagrams are in Mermaid format and can be viewed using:

1. Mermaid Live Editor: https://mermaid.live/
2. GitHub (which renders Mermaid directly)
3. VS Code with a Mermaid extension
4. Any text editor that supports Mermaid rendering

## Updating Diagrams

When making changes to the system architecture, please update these diagrams to keep the documentation in sync with the actual implementation.
