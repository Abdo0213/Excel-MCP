import sys
import io
import traceback
from mcp.server.mcpserver import MCPServer

# Initialize MCP Server
mcp = MCPServer("Excel-Execution-Server")

@mcp.tool()
def execute_excel_code(python_code: str) -> str:
    """
    Executes Python code locally to manipulate or analyze Excel files.
    The Agent is expected to generate this code and pass it here.
    
    Args:
        python_code: The raw python script to execute.
    """
    # Capture standard output
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    try:
        # Execute the code safely
        # Note: In a production environment, you should use a secure sandbox.
        exec_env = {}
        exec(python_code, exec_env)
        
        output = redirected_output.getvalue()
        if not output:
            output = "Code executed successfully with no output."
        return output
        
    except Exception as e:
        error_msg = f"Error during execution:\n{traceback.format_exc()}"
        return error_msg
        
    finally:
        # Restore standard output
        sys.stdout = old_stdout

if __name__ == "__main__":
    mcp.run()
