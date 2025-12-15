import asyncio
import logging
import os
import sys
import subprocess
import time
import random
from typing import Dict, Optional
from dataclasses import dataclass
from kirosu.client import SwarmClient

# ---------------- CONFIG ----------------
logging.basicConfig(level=logging.ERROR)
logging.getLogger("SwarmClient").setLevel(logging.ERROR)
logging.getLogger("root").setLevel(logging.ERROR)

HUB_PORT = 8790
DB_PATH = "kuopio.db"

# ----------------- GAME ENGINE -----------------

@dataclass
class Location:
    name: str
    npc_name: str
    description: str = "" # Static fallback

class GameState:
    def __init__(self):
        self.time = 18.0 # Starts at 18:00
        self.sober_level = 50 # 0-100
        self.clues_found = 0
        self.has_wallet = False
        self.phone_battery = 15
        self.identity_known = False
        self.friends_found = False
        self.at_cottage = False
        
    def advance_time(self, amount=0.5):
        self.time += amount
        self.phone_battery -= 2
        if self.time >= 24.0: self.time = 0.0

    def get_time_str(self):
        h = int(self.time)
        m = int((self.time - h) * 60)
        return f"{h:02d}:{m:02d}"

class KuopioWorld:
    def __init__(self):
        # 3x3 Grid centered on "Mualiman Napa" (The Tori)
        self.map: Dict[tuple, Location] = {}
        self.player_pos = (0, 0)
        
        # KEY LOCATIONS
        self.map[(0, 0)] = Location("Mualiman Napa (Tori)", "Toripolliisi", "Olet Kuopion torilla. Juhannusjuhlat ovat käynnissä.")
        self.map[(0, 1)] = Location("Kauppahalli", "Lihava Kalakukkomyyjä", "Halli on kiinni, mutta joku myy tiskin alta evästä.")
        self.map[(1, 0)] = Location("Hanna Partasen Jono", "Nälkäinen Teekkari", "Jono ulottuu nurkan taakse, tuoksu on huumaava.")
        self.map[(-1, 0)] = Location("Taksitolppa", "Kyllästynyt Kuski", "Mersut odottavat kyytiläisiä. Sinulla ei ole rahaa.")
        self.map[(0, -1)] = Location("Matkustajasatama", "Kapteeni Koukku", "Laivat soittavat sumutorvia. Kallavesj lainehtii.")
        
    def get_current_room(self) -> Optional[Location]:
        return self.map.get(self.player_pos)

    async def move(self, direction: str, client: SwarmClient) -> bool:
        x, y = self.player_pos
        if direction == "n": y += 1
        elif direction == "s": y -= 1
        elif direction == "e": x += 1
        elif direction == "w": x -= 1
        else: return False
        
        # Bounds
        if abs(x) > 3 or abs(y) > 3:
            print("🚫 Et jaksa kävellä pidemmälle, jalat on muussia.")
            return False

        # DYNAMIC GENERATION (Savo Flavor)
        if (x, y) not in self.map:
            print(f"✨ Harhailet tuntemattomalle kadulle ({x}, {y})...")
            # Ask LLM to invent a location
            resp = await ask_dm(client, 
                "Olet Savolainen Pelinjohtaja. Keksi lyhyt Kuopiolainen kadunkulma tai baari. Tulosta vain 2 riviä: Paikka, NPC nimi.",
                f"Generoi sijainti koordinaateille {x},{y}."
            )
            try:
                lines = [l.strip() for l in resp.strip().split('\n') if l.strip()]
                r_name = lines[0] if len(lines) > 0 else "Syrjäkuja"
                n_name = lines[1] if len(lines) > 1 else "Tuntematon Kulkija"
                self.map[(x, y)] = Location(r_name, n_name)
            except:
                self.map[(x, y)] = Location("Hämärä Puisto", "Sammnunut Juhlija")
            
        self.player_pos = (x, y)
        return True

# ----------------Kirosu Helpers ----------------

def start_process(cmd, name):
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy()
    )

async def ask_dm(client, system_context, player_input):
    full_prompt = f"""
System: Olet interaktiivinen tekstiseikkailu "Kuopion Juhannus".
Tyyli: Puhu leveää Savon murretta. Ole humoristinen mutta hiemankaoottinen.
Context: {system_context}

Game Event: {player_input}

Output (MAX 2 lines, Savo dialect):
"""
    task_id = await client.add_task(full_prompt, task_type="game")
    while True:
        await asyncio.sleep(0.3)
        status = await client._send_request("list", {"limit": 5}) 
        for t in status.get('tasks', []):
            if t['task_id'] == task_id and t['status'] == 'done':
                return t['result']

# ---------------- MAIN LOOP ----------------

async def game_loop():
    # Setup
    if os.path.exists(DB_PATH):
        try: os.remove(DB_PATH)
        except: pass
        
    print("🌭  Lämmitetään grilliä... (Starting Engine)")
    subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
    
    hub = start_process(
        [sys.executable, "-m", "kirosu.cli", "hub", "--port", str(HUB_PORT), "--db", DB_PATH], "Hub"
    )
    
    # Wait for Hub
    for _ in range(20):
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", HUB_PORT)
            writer.close()
            await writer.wait_closed()
            break
        except Exception:
            await asyncio.sleep(0.5)
    else: 
        print("❌ Engine Failed"); return

    # Start Agent
    agent = start_process(
        [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(HUB_PORT), "--id", "SAVO_DM", "--model", "gpt-5.1-codex-mini"],
        "GameMaster"
    )
    time.sleep(3)
    
    world = KuopioWorld()
    state = GameState()
    
    print("\n" + "="*60)
    print("🇫🇮  K U O P I O N   J U H A N N U S  🇫🇮")
    print(f"      Model: gpt-5.1-codex-mini (Savolais-moodilla)")
    print("   Liiku: n, s, e, w  |  Puhu: talk <asia>  |  Etsi: search  |  quit")
    print("="*60 + "\n")
    print("Tehtävä: Selvitä kuka olet, löydä lompakko ja pääse Mökille ennen aamua.")

    async with SwarmClient(port=HUB_PORT) as client:
        # Initial Look
        loc = world.get_current_room()
        intro = await ask_dm(client, 
            "Kuvaile aloitustilanne Kuopion torilla juhannusaattona. Pelaaja on hukassa.", 
            "Peli alkaa."
        )
        print(f"⏰ {state.get_time_str()} | 🔋 {state.phone_battery}% | {loc.name}")
        print(f"👁️  {intro}\n")

        while float(state.get_time_str().replace(":", ".")) < 24.0: # Simplified check
            try:
                cmd = input("👉 \033[1mTekee mieli\033[0m: ").strip().lower()
            except EOFError: break
            
            if cmd in ["quit", "exit"]: break
            
            # ACTION HANDLING
            state.advance_time(0.5) # Time flies when having fun
            
            if cmd in ["n", "s", "e", "w"]:
                if await world.move(cmd, client):
                    loc = world.get_current_room()
                    desc = await ask_dm(client, 
                        f"Kuvaile {loc.name}. Siellä on {loc.npc_name}.", 
                        f"Pelaaja saapuu paikkaan {loc.name}."
                    )
                    print(f"\n⏰ {state.get_time_str()} | 🔋 {state.phone_battery}% | 📍 {loc.name}")
                    print(f"👁️  {desc}\n")
            
            elif cmd.startswith("talk"):
                msg = cmd[5:].strip()
                loc = world.get_current_room()
                reply = await ask_dm(client, 
                    f"Olet {loc.npc_name}. Puhu leveää savoa. Pelaaja kysyy: {msg}", 
                    f"Pelaaja sanoo: {msg}"
                )
                print(f"🗣️  \033[33m{loc.npc_name}\033[0m: {reply}\n")
                
                # Check for Clues (Naive logic)
                if "kuka" in msg or "olen" in msg:
                   state.clues_found += 1
                   if state.clues_found >= 3:
                       state.identity_known = True
                       print("💡 \033[1;32mOIVALLUS!\033[0m Muistat nimesi: Olet Jartsa, Putkimies Nilsiästä.")
            
            elif cmd == "search":
                if random.random() < 0.3:
                     item = await ask_dm(client, "Keksi joku turha esine mitä maasta löytyy festareilla.", "Search")
                     print(f"🔎 Löysit jotain: {item} (Ei auta mihinkään)")
                elif not state.has_wallet and random.random() < 0.1:
                     state.has_wallet = True
                     print("🎉 \033[1;32mLÖYSIT LOMPAKKOSI!\033[0m Se oli lihapiirakan alla.")
                else:
                     print("🔎 Et löydä mitään järkevää. Vain lokkeja.")

            # Win Condition
            if state.identity_known and state.has_wallet and "taksi" in world.get_current_room().name.lower():
                 print("\n🚕 Hyppäät taksiin. 'Vie minut mökille, Nilsiään!'")
                 print("Peli Päättyi: VOITTO! Ehdit saunaan.")
                 break
            
            # Lose Condition
            if state.phone_battery <= 0:
                 print("\n🪫 Puhelimesta loppui akku. Et löydä enää ketään. Nukahdat penkille.")
                 print("GAME OVER.")
                 break

    # Cleanup
    hub.terminate()
    agent.terminate()
    subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
    if os.path.exists(DB_PATH):
        try: os.remove(DB_PATH)
        except: pass

if __name__ == "__main__":
    try:
        asyncio.run(game_loop())
    except (KeyboardInterrupt, asyncio.CancelledError):
        subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
        sys.exit(0)
