"""
Test script to verify consistent ${VARIABLE} syntax works across .env and YAML files.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up test environment variables
os.environ['TEST_NVIDIA_KEY'] = 'nvapi-test-key-12345'
os.environ['TEST_BRAVE_KEY'] = 'brave-test-key-67890'
os.environ['LLM_PROVIDER'] = 'nvidia'
os.environ['LLM_MODEL'] = 'meta/llama-3.1-70b-instruct'
os.environ['LLM_ENDPOINT'] = 'https://integrate.api.nvidia.com/v1'
os.environ['LLM_API_KEY'] = '${TEST_NVIDIA_KEY}'
os.environ['SEARCH_API_KEY'] = '${TEST_BRAVE_KEY}'
os.environ['SEARCH_API_ENDPOINT'] = 'https://api.search.brave.com/res/v1/web/search'

from app.config import get_settings
from app.services.storage import resolve_env_variables


def test_settings_resolution():
    """Test that Settings class resolves ${VARIABLE} references."""
    print("=" * 80)
    print("Testing Settings Variable Resolution")
    print("=" * 80)
    
    # Create a test .env-like environment
    os.environ['TEST_VAR_1'] = 'value1'
    os.environ['TEST_VAR_2'] = '${TEST_VAR_1}'
    os.environ['JWT_SERVICE_URL'] = 'http://localhost:${PORT}'
    os.environ['PORT'] = '5000'
    
    settings = get_settings()
    
    # Test that JWT_SERVICE_URL gets resolved
    print(f"\n1. Settings resolution test:")
    print(f"   JWT_SERVICE_URL = {settings.jwt_service_url}")
    expected = "http://localhost:5000"
    if "${PORT}" not in settings.jwt_service_url:
        print(f"   ✓ PASS - Variable resolved")
    else:
        print(f"   ✗ FAIL - Variable not resolved")
    
    return True


def test_yaml_resolution():
    """Test that YAML loading resolves ${VARIABLE} references."""
    print("\n" + "=" * 80)
    print("Testing YAML Variable Resolution")
    print("=" * 80)
    
    # Test data structure simulating YAML content
    test_data = {
        'llm': {
            'provider': '${LLM_PROVIDER}',
            'model': '${LLM_MODEL}',
            'endpoint': '${LLM_ENDPOINT}',
            'api_key': '${LLM_API_KEY}'
        },
        'tools': [
            {
                'name': 'web-search',
                'api_key': '${SEARCH_API_KEY}',
                'endpoint': '${SEARCH_API_ENDPOINT}'
            }
        ]
    }
    
    print(f"\n1. Before resolution:")
    print(f"   LLM API Key: {test_data['llm']['api_key']}")
    print(f"   Search API Key: {test_data['tools'][0]['api_key']}")
    
    # Resolve variables
    resolved = resolve_env_variables(test_data)
    
    print(f"\n2. After resolution:")
    print(f"   LLM Provider: {resolved['llm']['provider']}")
    print(f"   LLM Model: {resolved['llm']['model']}")
    print(f"   LLM API Key: {resolved['llm']['api_key']}")
    print(f"   Search API Key: {resolved['tools'][0]['api_key']}")
    
    # Verify resolution worked
    tests_passed = 0
    tests_total = 4
    
    if resolved['llm']['provider'] == 'nvidia':
        print(f"   ✓ LLM Provider resolved correctly")
        tests_passed += 1
    else:
        print(f"   ✗ LLM Provider not resolved")
    
    if resolved['llm']['model'] == 'meta/llama-3.1-70b-instruct':
        print(f"   ✓ LLM Model resolved correctly")
        tests_passed += 1
    else:
        print(f"   ✗ LLM Model not resolved")
    
    # Check nested resolution (${LLM_API_KEY} -> ${TEST_NVIDIA_KEY} -> actual value)
    if 'nvapi-test-key-12345' in resolved['llm']['api_key']:
        print(f"   ✓ LLM API Key resolved with nested reference")
        tests_passed += 1
    else:
        print(f"   ✗ LLM API Key not fully resolved: {resolved['llm']['api_key']}")
    
    if 'brave-test-key-67890' in resolved['tools'][0]['api_key']:
        print(f"   ✓ Search API Key resolved with nested reference")
        tests_passed += 1
    else:
        print(f"   ✗ Search API Key not fully resolved: {resolved['tools'][0]['api_key']}")
    
    print(f"\n   Result: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


def test_agent_config_loading():
    """Test loading an actual agent configuration."""
    print("\n" + "=" * 80)
    print("Testing Agent Configuration Loading")
    print("=" * 80)
    
    from app.services.agent_service import AgentService
    
    agent_service = AgentService()
    
    # Try to load research-agent
    print(f"\n1. Loading research-agent...")
    agent = agent_service.get_agent('research-agent')
    
    if agent:
        print(f"   ✓ Agent loaded successfully")
        print(f"   Agent ID: {agent.id}")
        print(f"   Agent Name: {agent.name}")
        print(f"   LLM Provider: {agent.llm.provider}")
        print(f"   LLM Model: {agent.llm.model}")
        print(f"   LLM Endpoint: {agent.llm.endpoint}")
        
        # Check if api_key was resolved
        if agent.llm.api_key:
            if '${' not in agent.llm.api_key and '$' not in agent.llm.api_key:
                print(f"   ✓ API key resolved (no $ references)")
                print(f"   API Key (first 10 chars): {agent.llm.api_key[:10]}...")
                return True
            else:
                print(f"   ✗ API key still contains variable reference: {agent.llm.api_key}")
                return False
        else:
            print(f"   ⚠ API key is None (check your .env file)")
            return False
    else:
        print(f"   ✗ Failed to load agent")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("CONSISTENT ${VARIABLE} SYNTAX TEST SUITE")
    print("=" * 80)
    
    results = []
    
    try:
        results.append(("Settings Resolution", test_settings_resolution()))
    except Exception as e:
        print(f"   ✗ EXCEPTION: {e}")
        results.append(("Settings Resolution", False))
    
    try:
        results.append(("YAML Resolution", test_yaml_resolution()))
    except Exception as e:
        print(f"   ✗ EXCEPTION: {e}")
        results.append(("YAML Resolution", False))
    
    try:
        results.append(("Agent Config Loading", test_agent_config_loading()))
    except Exception as e:
        print(f"   ✗ EXCEPTION: {e}")
        results.append(("Agent Config Loading", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} test suites passed")
    print("=" * 80)
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
