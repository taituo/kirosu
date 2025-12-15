# Chapter 03: Beyond Enterprise - Creative Agents & Simulations

> "Stop thinking about 'Business Logic' for a second. Let's make the AI hallucinate a 1997 web browser."

While Kirosu is designed for robust enterprise swarms, the same architecture can be used to build immersive simulations, games, and creative tools. In this chapter, we explore how to bend the **Orchestrator Pattern** to create **Experience Engines**.

We will cover the "Wild Demos" built during our prototyping session:
1.  **The Savonian Survival** (Persona Injection)
2.  **The Dungeon Master** (Stateful Game Loops)
3.  **The Retro Web** (TUI & Style Transfer)

---

## 1. Persona Injection: "Kuopion Tori"

Most enterprise agents are instructed to be "helpful and concise". For creative agents, we want the opposite: **Personality**.

In `examples/kuopion_tori.py`, we created a text adventure set in Kuopio Market Square. The key was a violently specific System Prompt.

### The Code Pattern
Instead of asking for a generic response, we inject a "Persona Filter":

```python
SYSTEM_PROMPT = """
ROLE: Game Master (Savonian Context)
SETTING: Kuopio Market Square, Midsummer Eve.
DIALECT: Heavy Savonian Finnish ("Viäntää").
GOAL: The user is "Jartsa", lost and drunk. He needs his wallet.

RULES:
1. Never break character.
2. Every NPC must speak with a thick dialect.
3. If the user tries to leave without the wallet, block them with a humorous event.
"""
```

### Why it works
The LLM treats the "Dialect" and "Setting" as conversational constraints just like "JSON output". By defining the *world state* (Midsummer, Drunk Jartsa) in the prompt, the Agent becomes a simulated reality engine.

---

## 2. Stateful Interaction: The Dungeon Crawler

In `examples/dungeon_crawl.py`, we proved that LLMs can manage game logic (HP, Inventory) if you provide the state in every turn.

### The "Game Loop" Architecture
A stateless agent cannot remember that you picked up a sword 3 turns ago. You must feed the state back to it.

```python
# The Loop
while player.hp > 0:
    # 1. State Injection
    context = f"""
    LOCATION: {player.x}, {player.y}
    HP: {player.hp}/100
    INVENTORY: {', '.join(player.inventory)}
    VISIBLE: {room.description}
    """
    
    # 2. Agent Decision
    response = await agent.ask(context + "\nUser Action: " + user_input)
    
    # 3. State Update (Parsing)
    if "ATTACK" in response:
        monster.hp -= 10
```

**Key Lesson**: Don't rely on the LLM's memory. **You** are the database. The LLM is just the rendering engine and logic processor.

---

## 3. The Retro Web: Style Transfer as UI

We built three "Browsers" that don't actually browse the web (mostly):
*   **Lynx 1997 Simulator**
*   **Teletext Simulator**
*   **Real AI Browser**

### The "Hallucination Feature"
For the Lynx Simulator (`examples/internet_dsl_lynx.py`), we didn't want real data. We wanted the *vibe* of 1997.

**Prompting for Aesthetics:**
```text
Style: "Under Construction" banners, WebRings, Guestbooks.
Topics: X-Files, Spice Girls, GeoCities.
Constraint: Use simplistic HTML mental model.
```

The Agent successfully hallucinated convincing 90s fan pages because it has seen millions of them in its training data.

### The "Real" Browser & Safety Filters
For `examples/real_browser.py`, we wanted actual data. But the model refused, saying "I am an AI, I cannot browse."

** The Fix: "Boring Mode" **
To bypass refusal, we changed the prompt from specific roleplay ("You are a Browser") to generic labor ("PERFORM WEB RETRIEVAL TASK").

```diff
- You are a Text-Mode Web Browser.
+ PERFORM WEB RETRIEVAL TASK. Target: {url}.
```

**Lesson**: If an Agent refuses a creative task, frame it as a boring data processing job. It will usually comply.

---

## 4. Summary: The Creative Stack

Building creative agents requires a different mindset than enterprise tooling:

| Interface | Enterprise | Creative |
| :--- | :--- | :--- |
| **Prompting** | Helpful, Neutral | Opinionated, Stylized |
| **State** | database_id | Inventory, HP, Sanity |
| **UI** | JSON/REST | TUI, ASCII, Narratives |
| **Goal** | Efficiency | Immersion |

Go forth and build weird things. The Enterprise can wait.
