import json
import logging
import os
import subprocess
from typing import Dict, Any

from .topology_defs import get_topology_context, TOPOLOGIES

SUGGEST_SYSTEM_PROMPT = f"""
You are an expert AI Agent Architect for the Kirosu Swarm Orchestrator.
Your goal is to analyze the user's task description and recommend the single best agent TOPOLOGY.

Here are the available topologies you can choose from:

{get_topology_context()}

INSTRUCTIONS:
1. Analyze the complexity, dependencies, and nature of the user's request.
2. Select the most appropriate topology from the list above.
3. Explain your reasoning briefly (why this topology?).
4. Provide a sample `kirosu` command to execute this strategy.
5. Return your response in the following JSON format ONLY:

{{
  "topology": "<key_from_list_above>",
  "reasoning": "<your_explanation>",
  "command": "<kirosu_cli_command_suggestion>"
}}

Valid topology keys are: {', '.join(TOPOLOGIES.keys())}.
DO NOT wrap the output in markdown code blocks. Return raw JSON.
"""

from .providers import get_provider

def suggest_strategy(task_description: str) -> Dict[str, Any]:
    """
    Uses the configured LLM Provider to analyze the task and suggest a strategy.
    """
    # Prompt construction
    full_prompt = f"Recommend a topology for this task: {task_description}"
    
    try:
        logging.info("Requesting strategy suggestion from LLM Provider...")
        
        provider_name = os.environ.get("KIRO_PROVIDER")
        model = os.environ.get("MITTELO_KIRO_MODEL", "claude-haiku-4.5")
        
        provider = get_provider(provider_name, model)
        output = provider.run(full_prompt, system_prompt=SUGGEST_SYSTEM_PROMPT)

        if not output:
             return {
                "error": "LLM call returned empty response",
                "topology": "single",
                "command": f"kirosu agent --id single_worker"
            }

        output = output.strip()
        
        # Extremely basic cleanup if the LLM adds markdown blocks despite instructions
        if output.startswith("```json"):
            output = output[7:]
        if output.startswith("```"):
            output = output[3:]
        if output.endswith("```"):
            output = output[:-3]
        
        try:
            result = json.loads(output)
            return result
        except json.JSONDecodeError:
             return {
                "error": "Failed to parse LLM response",
                "raw_response": output,
                "topology": "unknown"
            }

    except Exception as e:
        logging.error(f"suggest_strategy failed: {e}")
        return {
            "error": str(e),
            "topology": "single"
        }

def print_strategy_suggestion(task_description: str):
    """
    Pretty prints the suggestion to the console.
    """
    print(f"🔍 Analyzing task: '{task_description}'...")
    suggestion = suggest_strategy(task_description)

    if "error" in suggestion and "raw_response" not in suggestion:
         print(f"❌ Error: {suggestion['error']}")
         return

    topo_key = suggestion.get("topology", "single")
    topo_def = TOPOLOGIES.get(topo_key)
    
    print("\n" + "="*60)
    print(f"💡 RECOMMENDATION: {topo_def.name if topo_def else topo_key.upper()}")
    print("="*60)
    
    if topo_def:
        print(topo_def.ascii_art)
    
    print(f"\n🧠 REASONING:\n{suggestion.get('reasoning', 'No reasoning provided.')}")
    
    print(f"\n🚀 COMMAND:\n{suggestion.get('command', 'No command provided.')}")
    
    if "raw_response" in suggestion:
        print(f"\n⚠️ (Raw response was not valid JSON):\n{suggestion['raw_response']}")

    print("\n" + "="*60)

def print_available_strategies():
    """
    Prints a table of available strategies.
    """
    print(f"\n{'STRATEGY':<20} | {'DESCRIPTION':<60}")
    print("-" * 85)
    for key, topo in TOPOLOGIES.items():
        print(f"{topo.name:<20} | {topo.description:<60}")
    print("-" * 85)
    print("\nUse 'kirosu suggest <task>' to get a specific recommendation.")

class RecursiveStrategy:
    """
    Implements a meta-strategy where a 'Planner Agent' decides the execution plan,
    which is then automatically executed by the system.
    """
    
    PLANNER_SYSTEM_PROMPT = """
You are the Chief Architect for a Kirosu Swarm. 
Your goal is to accept a high-level objective and output a valid Kirosu Pipeline Configuration (YAML) to solve it.

The available agent modules are: 
- `agents.general_worker` (generic tasks)
- `agents.researcher` (web search/analysis)
- `agents.coder` (software engineering)

Output ONLY the YAML configuration block. Do not add markdown backticks.
The YAML format is:
pipeline:
  - id: step_1
    module: agents.general_worker
    config:
      prompt: "Specific instruction for this step"
  - id: step_2
    module: agents.general_worker
    depends_on: [step_1]
    config:
      prompt: "Instruction using previous results"
"""

    @staticmethod
    def execute(task_description: str):
        """
        1. Runs a Planner Agent to generate a YAML pipeline.
        2. Executes the generated pipeline.
        """
        logging.info(f"RecursiveStrategy: Planning task '{task_description}'...")
        
        logging.info(f"RecursiveStrategy: Planning task '{task_description}'...")
        
        # Step 1: Planning
        try:
            provider_name = os.environ.get("KIRO_PROVIDER")
            model = os.environ.get("MITTELO_KIRO_MODEL", "claude-haiku-4.5")
            provider = get_provider(provider_name, model)
            
            yaml_plan = provider.run(f"Create a plan for: {task_description}", system_prompt=RecursiveStrategy.PLANNER_SYSTEM_PROMPT)
            
            if not yaml_plan:
                raise RuntimeError("Planner returned empty response")
            # Cleanup common markdown issues
            if yaml_plan.startswith("```yaml"): yaml_plan = yaml_plan[7:]
            if yaml_plan.startswith("```"): yaml_plan = yaml_plan[3:]
            if yaml_plan.endswith("```"): yaml_plan = yaml_plan[:-3]
            
            plan_file = "recursive_plan.yml"
            with open(plan_file, "w") as f:
                f.write(yaml_plan)
                
            logging.info(f"RecursiveStrategy: Plan generated saved to {plan_file}")
            print(f"📋 Plan generated:\n{yaml_plan}")
            
            # Step 2: Execution (Invoking the pipeline runner - simulated here for CLI capability)
            logging.info("RecursiveStrategy: Executing plan...")
            
            env = os.environ.copy()
            exec_cmd = ["kirosu", "run-pipeline", "--file", plan_file]
            subprocess.run(exec_cmd, check=True, env=env)
            
            logging.info("RecursiveStrategy: Execution complete.")
            
        except Exception as e:
            logging.error(f"RecursiveStrategy failed: {e}")
            print(f"❌ Error: {e}")
