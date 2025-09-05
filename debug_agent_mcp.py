"""
Debug agent MCP communication - check what's actually happening
"""
import json
import subprocess
import sys

def debug_agent_mcp_call():
    """Debug exactly what the agent is doing"""
    print("Starting MCP server...")
    
    process = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        print("=== What the AGENT is doing (without initialization) ===")
        
        # This is what the agent is currently doing - jumping straight to tools/call
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
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
        
        print("Agent sending:", json.dumps(mcp_request, indent=2))
        process.stdin.write(json.dumps(mcp_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        print("Agent received:", response)
        
        if response:
            try:
                response_data = json.loads(response)
                print("Parsed response:", json.dumps(response_data, indent=2))
                
                # Check what the agent's parsing logic sees
                if "result" in response_data:
                    print("✓ Found 'result' key")
                    if "content" in response_data["result"]:
                        print("✓ Found 'content' key")
                        if len(response_data["result"]["content"]) > 0:
                            print("✓ Found content array items")
                            content = response_data["result"]["content"][0]["text"]
                            print("✓ Extracted text content")
                            final_result = json.loads(content)
                            print("✓ SUCCESS - Final parsed result:")
                            print(json.dumps(final_result, indent=2))
                        else:
                            print("✗ Empty content array")
                    else:
                        print("✗ No 'content' key in result")
                else:
                    print("✗ No 'result' key - this is why agent says 'Invalid MCP response'")
                    if "error" in response_data:
                        print(f"✗ Error in response: {response_data['error']}")
                        
            except json.JSONDecodeError as e:
                print(f"✗ JSON parse error: {e}")
        else:
            print("✗ No response received")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    debug_agent_mcp_call()