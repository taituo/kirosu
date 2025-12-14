---
description: Agentic Workflow Strategy
---

# Agentic Workflow Strategy

This workflow outlines how to transition from using AI as a tool (10-30% productivity gain) to using AI as an agentic workforce (3x-10x productivity gain).

## 1. Mindset Shift: From Tool to Team
- **Don't** just ask for a single output (e.g., "Write an email").
- **Do** assign a role and a goal (e.g., "You are my PR manager. Manage this communication channel independently.").
- **Goal**: Remove yourself from the loop as much as possible.

## 2. Define Agent Roles
Categorize your agents into three types:

### A. Assistant Agents
- **Function**: Handle simple, linear tasks.
- **Examples**: Booking flights, calendar management, simple research.
- **Tools**: Web search, Calendar API.

### B. Worker Agents
- **Function**: Execute complex task sets and coordinate.
- **Examples**: Coding a feature, writing a report, analyzing data.
- **Topology**: Can work in groups (swarms).

### C. Thinker Agents
- **Function**: Elevate reasoning and decision making.
- **Pattern**: **Generator + Judge**.
    1.  **Generator**: Proposes ideas/solutions.
    2.  **Judge**: Critically evaluates based on strict criteria (axiomatic, non-sycophantic).
    3.  **Loop**: Iterate until the Judge approves.

## 3. Design the Topology
Choose how your agents interact:
- **Hierarchy**: Orchestrator delegates to Workers. Best for clear project management.
- **Mesh**: Agents work independently but request help from others.
- **Ring**: Sequential processing (Agent A -> Agent B -> Agent C).
- **DAG (Directed Acyclic Graph)**: Complex process automation with dependencies.

## 4. Implementation Strategy (The "Metaprompting" Technique)
Don't write the final prompt yourself. Use AI to write the prompt for the agent.

1.  **Define the Goal**: "I need an advisor for X."
2.  **Metaprompt**: Ask a high-level model (e.g., Gemini/Claude):
    > "Write a prompt for an AI agent that acts as the world's best expert in [Field]. It must be critical, axiomatic, and never sycophantic. It should challenge my assumptions."
3.  **Instantiate**: Use the generated prompt to initialize your "Thinker" or "Advisor" agent.

## 5. Execution & Grounding
- **Deep Research**: Always ground "Thinker" agents with a "Researcher" agent that has access to the internet (e.g., Perplexity or custom search tools) to fetch current facts.
- **Parallelization**: Run multiple agents simultaneously to solve different parts of a problem (e.g., one researches pros, one researches cons, one synthesizes).

## 6. Continuous Transformation (AI Native)
- **Audit**: List all daily tasks.
- **Ask**: "Which of these can be fully automated by an agent?"
- **Transform**: Redesign the process. Don't just automate the human process; ask if the process is needed at all or if an agent can achieve the *outcome* differently.