from app.services.storage import StorageService
from app.models.agents import AgentConfig
import traceback

storage = StorageService('./data/agents', AgentConfig, 'yaml')

print("Attempting to load database-analyst agent...")
try:
    agent = storage.load('database-analyst')
    if agent:
        print(f"✓ Success! Agent ID: {agent.id}")
        print(f"  Name: {agent.name}")
        print(f"  LLM Provider: {agent.llm.provider if agent.llm else 'None'}")
    else:
        print("✗ Agent returned None")
except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()
