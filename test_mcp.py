"""
Test MCP server communication directly
"""
import asyncio
import json
import subprocess
import sys

async def test_mcp_server():
    """Test MCP server communication"""
    print("Starting MCP server...")
    
    # Start MCP server
    process = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # First, we need to initialize the MCP connection
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read initialize response
        response = process.stdout.readline()
        print(f"Initialize response: {response}")
        
        if response:
            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            
            print("Sending initialized notification...")
            process.stdin.write(json.dumps(initialized_notification) + "\n")
            process.stdin.flush()
            
            # Now test list tools
            list_tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            print("Sending list tools request...")
            process.stdin.write(json.dumps(list_tools_request) + "\n")
            process.stdin.flush()
            
            response = process.stdout.readline()
            print(f"List tools response: {response}")
            
            if response:
                # Test weather tool
                weather_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "weather_api",
                        "arguments": {
                            "location": "Sydney",
                            "forecast_days": 1,
                            "include_hourly": True
                        }
                    }
                }
                
                print("Sending weather API request...")
                process.stdin.write(json.dumps(weather_request) + "\n")
                process.stdin.flush()
                
                response = process.stdout.readline()
                print(f"Weather API response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())