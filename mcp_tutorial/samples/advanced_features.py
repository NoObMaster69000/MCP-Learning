from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
import asyncio

mcp = FastMCP("AdvancedFeatures")

# 1. Using Pydantic models for complex inputs
class UserProfile(BaseModel):
    username: str = Field(..., description="The user's unique username")
    age: int = Field(..., gt=0, description="The user's age in years")
    interests: list[str] = Field(default_factory=list, description="List of user interests")

@mcp.tool()
def update_profile(profile: UserProfile) -> str:
    """Updates a user profile with structured data."""
    return f"Updated profile for {profile.username} (Age: {profile.age}). Interests: {', '.join(profile.interests)}"

# 2. Using the Context object for progress and logging
@mcp.tool()
async def long_running_task(iterations: int, ctx: Context) -> str:
    """A task that reports progress back to the client."""
    for i in range(iterations):
        await asyncio.sleep(0.5)
        # Report progress (if supported by the client)
        await ctx.report_progress(i + 1, iterations)
        # Log to the client
        await ctx.info(f"Completed iteration {i+1} of {iterations}")

    return f"Completed {iterations} iterations successfully."

# 3. Dynamic Resources with Templates
@mcp.resource("config://{env}/settings.json")
def get_config(env: str) -> str:
    """Returns configuration based on the environment."""
    configs = {
        "dev": '{"debug": true, "database": "localhost"}',
        "prod": '{"debug": false, "database": "db.production.internal"}'
    }
    return configs.get(env, '{"error": "Environment not found"}')

if __name__ == "__main__":
    mcp.run()
