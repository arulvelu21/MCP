import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servers.jira import mcp

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8002)
