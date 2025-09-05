"""
Simple test of agent with MCP tools - no interactive chat
"""
import asyncio
from agent import WhatToDoAgent

async def test_single_query():
    """Test a single query without the interactive chat loop"""
    agent = WhatToDoAgent()
    
    try:
        # Start MCP server
        await agent.start_mcp_server()
        
        # Test a single query
        query = "What can I do tomorrow in Sydney?"
        print(f"Testing query: {query}")
        
        response = await agent.agent_loop(query)
        print("\n=== FINAL RESPONSE ===")
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        if agent.mcp_server_process:
            agent.mcp_server_process.terminate()
            agent.mcp_server_process.wait()

if __name__ == "__main__":
    asyncio.run(test_single_query())