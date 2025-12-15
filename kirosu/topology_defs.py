from typing import Dict, NamedTuple

class TopologyDef(NamedTuple):
    name: str
    description: str
    ascii_art: str
    usage_guidance: str

TOPOLOGIES: Dict[str, TopologyDef] = {
    "single": TopologyDef(
        name="Single Agent",
        description="One agent performs a single, well-defined task.",
        ascii_art="""
[ User ] -> [ Agent ] -> [ Result ]
""",
        usage_guidance="Use when the task is simple, self-contained, and linear (e.g., 'Update README', 'Fix typo')."
    ),
    "chain": TopologyDef(
        name="Linear Chain",
        description="Sequential execution where the output of one agent becomes the input of the next.",
        ascii_art="""
[ User ] -> [ Step 1 ] -> [ Step 2 ] -> [ Step 3 ] -> [ Result ]
""",
        usage_guidance="Use when the task has clear, dependent stages (e.g., 'Research -> Outline -> Write -> Review')."
    ),
    "parallel": TopologyDef(
        name="Parallel Swarm",
        description="Multiple agents working simultaneously on split tasks, aggregated at the end.",
        ascii_art="""
           /-> [ Agent A ] -\\
[ User ] -+--> [ Agent B ] --+-> [ Aggregator ] -> [ Result ]
           \\-> [ Agent C ] -/
""",
        usage_guidance="Use when the task involves analyzing multiple data sources or perspectives (e.g., 'Analyze 10 files', 'Tech/Biz/Risk review')."
    ),
    "iterative": TopologyDef(
        name="Iterative Swarm",
        description="A feedback loop between creators and reviewers to refine a result.",
        ascii_art="""
[ User ] -> [ Ideator ] --(draft)--> [ Reviewer ]
                 ^                        |
                 |_______(feedback)_______|
""",
        usage_guidance="Use for open-ended or creative tasks requiring quality control (e.g., 'Write a blog post', 'Design a system')."
    ),
    "autonomous": TopologyDef(
        name="Autonomous Swarm",
        description="Agents operating with autonomy within defined boundaries and rules.",
        ascii_art="""
[ Objective ] -> [ Worker ] <--> [ Environment ]
                    |
               [ Monitor ] -> [ Stop Signal ]
""",
        usage_guidance="Use for dynamic environments or simulations (e.g., 'Monitor logs and fix known errors', 'Game simulation')."
    )
}

def get_topology_context() -> str:
    """Returns a formatted string of all topology definitions for the LLM prompt."""
    output = []
    for key, topo in TOPOLOGIES.items():
        output.append(f"NAME: {topo.name} (Key: {key})")
        output.append("DIAGRAM:")
        output.append(topo.ascii_art.strip())
        output.append(f"DESCRIPTION: {topo.description}")
        output.append(f"WHEN TO USE: {topo.usage_guidance}")
        output.append("-" * 40)
    return "\\n".join(output)
