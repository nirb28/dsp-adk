"""
Test script for the Image Analysis Tool.
"""
import requests
import json
import sys

# Configuration
ADK_URL = "http://localhost:8100"
TOOL_ID = "image_analysis"

def test_tool_exists():
    """Test if the tool is registered."""
    print("\n" + "="*80)
    print("TEST 1: Check if tool exists")
    print("="*80)
    
    response = requests.get(f"{ADK_URL}/tools/{TOOL_ID}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✓ Tool '{TOOL_ID}' found")
            print(f"  Name: {data['tool']['name']}")
            print(f"  Description: {data['tool']['description']}")
            print(f"  Type: {data['tool']['tool_type']}")
            return True
        else:
            print(f"✗ Tool exists but returned success=false")
            return False
    else:
        print(f"✗ Tool not found (HTTP {response.status_code})")
        return False


def test_tool_schema():
    """Test getting the tool schema."""
    print("\n" + "="*80)
    print("TEST 2: Get tool schema")
    print("="*80)
    
    response = requests.get(f"{ADK_URL}/tools/{TOOL_ID}/schema")
    
    if response.status_code == 200:
        schema = response.json()
        print(f"✓ Schema retrieved successfully")
        print(f"  Function name: {schema['function']['name']}")
        print(f"  Parameters: {list(schema['function']['parameters']['properties'].keys())}")
        return True
    else:
        print(f"✗ Failed to get schema (HTTP {response.status_code})")
        return False


def test_general_analysis():
    """Test general image analysis."""
    print("\n" + "="*80)
    print("TEST 3: Execute general analysis (mock mode)")
    print("="*80)
    
    payload = {
        "arguments": {
            "image_path": "/test/image.jpg",
            "analysis_type": "general"
        },
        "mock": True
    }
    
    response = requests.post(
        f"{ADK_URL}/tools/{TOOL_ID}/execute",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            result = data["result"]
            print(f"✓ General analysis completed")
            print(f"  Analysis type: {result.get('analysis_type')}")
            print(f"  Success: {result.get('success')}")
            if result.get('results'):
                print(f"  Results: {json.dumps(result['results'], indent=2)}")
            return True
        else:
            print(f"✗ Analysis failed: {data.get('error')}")
            return False
    else:
        print(f"✗ Request failed (HTTP {response.status_code})")
        print(f"  Response: {response.text}")
        return False


def test_all_analysis_types():
    """Test all analysis types in mock mode."""
    print("\n" + "="*80)
    print("TEST 4: Test all analysis types")
    print("="*80)
    
    analysis_types = [
        "general",
        "object_detection",
        "text_extraction",
        "face_detection",
        "image_classification",
        "color_analysis",
        "quality_assessment"
    ]
    
    results = {}
    for analysis_type in analysis_types:
        payload = {
            "arguments": {
                "image_path": "/test/image.jpg",
                "analysis_type": analysis_type
            },
            "mock": True
        }
        
        response = requests.post(
            f"{ADK_URL}/tools/{TOOL_ID}/execute",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"  ✓ {analysis_type}")
                results[analysis_type] = True
            else:
                print(f"  ✗ {analysis_type}: {data.get('error')}")
                results[analysis_type] = False
        else:
            print(f"  ✗ {analysis_type}: HTTP {response.status_code}")
            results[analysis_type] = False
    
    success_count = sum(1 for v in results.values() if v)
    print(f"\n  Summary: {success_count}/{len(analysis_types)} analysis types working")
    return success_count == len(analysis_types)


def test_list_tools():
    """Test listing all tools."""
    print("\n" + "="*80)
    print("TEST 5: List all tools")
    print("="*80)
    
    response = requests.get(f"{ADK_URL}/tools")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            tools = data.get("tools", [])
            print(f"✓ Found {len(tools)} tools")
            
            # Check if our tool is in the list
            tool_ids = [t["id"] for t in tools]
            if TOOL_ID in tool_ids:
                print(f"  ✓ '{TOOL_ID}' is in the list")
                return True
            else:
                print(f"  ✗ '{TOOL_ID}' not found in tool list")
                print(f"  Available tools: {tool_ids}")
                return False
        else:
            print(f"✗ List tools returned success=false")
            return False
    else:
        print(f"✗ Failed to list tools (HTTP {response.status_code})")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("IMAGE ANALYSIS TOOL - TEST SUITE")
    print("="*80)
    print(f"ADK Server: {ADK_URL}")
    print(f"Tool ID: {TOOL_ID}")
    
    tests = [
        ("Tool Exists", test_tool_exists),
        ("Tool Schema", test_tool_schema),
        ("General Analysis", test_general_analysis),
        ("All Analysis Types", test_all_analysis_types),
        ("List Tools", test_list_tools)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ Test '{test_name}' raised exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
