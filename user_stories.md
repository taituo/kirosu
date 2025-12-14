# User Stories

## Core Functionality
- **As a developer**, I want to run a swarm of agents that can execute `kiro-cli` commands so that I can automate complex tasks.
- **As a developer**, I want to enqueue tasks with a prompt and an optional system prompt so that I can control the agent's persona and context.
- **As a developer**, I want the agents to run without sandboxing so that they can perform stateful operations like `kiro-cli login` and file system modifications.

## Workflow & Orchestration
- **As a user**, I want to define "Thinker" workflows where one agent generates ideas and another judges them, so that I can improve the quality of the output.
- **As a user**, I want to run agents in specific working directories so that I can isolate their file operations or operate on specific projects.

## Reliability & Testing
- **As a developer**, I want the system to handle race conditions in the database so that multiple agents can lease tasks without conflict.
- **As a developer**, I want to run full system tests with dynamic ports so that I can verify functionality without port conflicts.
- **As a developer**, I want to see code coverage metrics so that I can ensure the system is well-tested.

## API & Integration
- **As a developer**, I want to import `KiroAgent` and `HubClient` in my Python scripts so that I can build custom workflows programmatically.
