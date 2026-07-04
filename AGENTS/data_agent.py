from mcp_client import MCPClient

SERVER_PATH = os.path.join(os.path.dirname(__file__), "..", "TEXT_TO_SQL_AGENT", "main_mcp.py")
SERVER_PATH = os.path.abspath(SERVER_PATH)
print(f"Connecting to MCP server: {server_path}")

client = MCPClient(command="python", args=[server_path])
def get_tools():
    return f"\nConnected! Available tools: {client.get_tool_names_and_description()}"

