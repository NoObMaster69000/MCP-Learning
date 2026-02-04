import os
import logging
from fastmcp import FastMCP

# Configure logging to stderr so it doesn't interfere with stdio transport
logging.basicConfig(level=logging.INFO)

# Create an MCP server instance
mcp = FastMCP("KnowledgeAssistant")

# Mock data directory
NOTES_DIR = "my_notes"
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)
    # Create a sample note
    with open(os.path.join(NOTES_DIR, "welcome.md"), "w") as f:
        f.write("# Welcome to MCP\nThis is a sample note in your Knowledge Assistant.")

@mcp.tool()
def list_notes() -> list[str]:
    """Lists all markdown notes available in the system."""
    logging.info("Listing notes...")
    if not os.path.exists(NOTES_DIR):
        return []
    return [f for f in os.listdir(NOTES_DIR) if f.endswith('.md')]

@mcp.tool()
def read_note(filename: str) -> str:
    """
    Reads the content of a specific markdown note.

    Args:
        filename: The name of the file to read (including .md extension).
    """
    logging.info(f"Reading note: {filename}")
    path = os.path.join(NOTES_DIR, filename)

    # Simple security check to prevent directory traversal
    if ".." in filename or filename.startswith("/"):
        return "Error: Invalid filename. Only local notes can be read."

    if not os.path.exists(path):
        return f"Error: Note '{filename}' not found."

    with open(path, 'r') as f:
        return f.read()

@mcp.resource("notes://index")
def get_notes_index() -> str:
    """Returns a formatted list of all notes as a resource."""
    notes = list_notes()
    if not notes:
        return "No notes found."
    return "Available Notes:\n" + "\n".join([f"- {n}" for n in notes])

@mcp.prompt()
def summarize_note_prompt(filename: str) -> str:
    """Creates a prompt for the LLM to summarize a specific note."""
    return f"Please read the content of '{filename}' using the read_note tool and then provide a concise summary of its main points."

if __name__ == "__main__":
    # Start the server using stdio transport by default
    mcp.run()
