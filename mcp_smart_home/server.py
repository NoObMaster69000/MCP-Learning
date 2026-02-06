import json
import logging
import os
from datetime import datetime
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

# Setup logging to stderr
logging.basicConfig(level=logging.INFO)

# Initialize FastMCP server
mcp = FastMCP("SmartHomeManager")

# Mock database state
STATE_FILE = "mcp_smart_home/data/state.json"
LOG_FILE = "mcp_smart_home/data/home.log"

def ensure_data():
    if not os.path.exists("mcp_smart_home/data"):
        os.makedirs("mcp_smart_home/data")
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump({
                "lights": {"living_room": False, "kitchen": False, "bedroom": True},
                "temperature": 22.5,
                "thermostat": 21.0,
                "security_armed": False
            }, f)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write(f"[{datetime.now()}] System Initialized\n")

def get_state():
    ensure_data()
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def add_log(message):
    ensure_data()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now()}] {message}\n")

# --- Tools ---

@mcp.tool()
def list_devices() -> dict:
    """Lists all smart home devices and their current status."""
    return get_state()

@mcp.tool()
async def set_light(room: str, power: bool, ctx: Context) -> str:
    """
    Toggles a light in a specific room.

    Args:
        room: The room name (e.g., 'living_room', 'kitchen').
        power: True to turn on, False to turn off.
    """
    state = get_state()
    if room not in state["lights"]:
        return f"Error: Room '{room}' not found in lighting system."

    state["lights"][room] = power
    save_state(state)

    msg = f"Turned {'on' if power else 'off'} light in {room}"
    add_log(msg)
    await ctx.info(msg)
    return msg

@mcp.tool()
def set_thermostat(target_temp: float = Field(..., ge=15.0, le=30.0)) -> str:
    """
    Sets the target temperature for the house.

    Args:
        target_temp: Target temperature in Celsius (15-30).
    """
    state = get_state()
    state["thermostat"] = target_temp
    save_state(state)

    msg = f"Thermostat set to {target_temp}°C"
    add_log(msg)
    return msg

# --- Resources ---

@mcp.resource("home://status")
def get_home_status() -> str:
    """Returns a human-readable summary of the home status."""
    state = get_state()
    lights_on = [r for r, p in state["lights"].items() if p]
    return (
        f"Smart Home Status Summary:\n"
        f"- Temperature: {state['temperature']}°C\n"
        f"- Thermostat: {state['thermostat']}°C\n"
        f"- Lights On: {', '.join(lights_on) if lights_on else 'None'}\n"
        f"- Security: {'ARMED' if state['security_armed'] else 'DISARMED'}"
    )

@mcp.resource("home://logs")
def get_recent_logs() -> str:
    """Returns the last 10 entries from the system log."""
    ensure_data()
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
        return "".join(lines[-10:])

# --- Prompts ---

@mcp.prompt()
def morning_routine_prompt() -> str:
    """Standard morning routine workflow."""
    return (
        "Good morning! Please perform the following steps:\n"
        "1. Check the current home status using the 'home://status' resource.\n"
        "2. Turn on the kitchen lights.\n"
        "3. Set the thermostat to 22 degrees.\n"
        "4. Provide a summary of the actions taken."
    )

if __name__ == "__main__":
    mcp.run()
