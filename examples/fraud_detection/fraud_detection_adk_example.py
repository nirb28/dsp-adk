"""
Check Fraud Detection Example using ADK Server Endpoint

This example demonstrates fraud detection using the ADK server's agent execution:
1. Calls the ADK server API to execute an agent with fraud detection tools
2. The agent uses the image_fraud_detector tool through the ADK framework
3. Provides detailed logging of the entire process

Requirements:
- ADK server running (default: http://localhost:8100)
- Fraud detection agent configured in ADK
- Sample check images and signature samples
- Environment variables configured
"""

import os
import sys
import json
import logging
import httpx
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure detailed logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fraud_detection_adk.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Set console encoding to UTF-8 for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)


class ADKFraudDetectionClient:
    """
    Client for executing fraud detection through ADK server.
    
    Uses the ADK agent execution API to run fraud detection analysis
    with specialized tools for signature, watermark, and tampering detection.
    """
    
    def __init__(self, adk_url: str = "http://localhost:8100", agent_id: str = "fraud-detection-agent"):
        """
        Initialize the ADK client.
        
        Args:
            adk_url: Base URL of the ADK server
            agent_id: ID of the fraud detection agent
        """
        self.adk_url = adk_url.rstrip('/')
        self.agent_id = agent_id
        self.client = httpx.Client(timeout=120.0)
        
        logger.info("=" * 80)
        logger.info("INITIALIZING ADK FRAUD DETECTION CLIENT")
        logger.info("=" * 80)
        logger.info(f"ADK Server: {self.adk_url}")
        logger.info(f"Agent ID: {self.agent_id}")
        logger.info("=" * 80)
    
    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()
    
    def analyze_check(
        self,
        check_image: str,
        comparison_signatures: List[str] = None,
        expected_watermark: str = None,
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run fraud detection analysis through ADK server.
        
        Args:
            check_image: Path to check image
            comparison_signatures: Paths to known valid signatures
            expected_watermark: Expected watermark description
            focus_areas: Areas to focus tampering detection
            
        Returns:
            Analysis results from the agent
        """
        logger.info("")
        logger.info("=" * 80)
        logger.info("STARTING ADK FRAUD DETECTION ANALYSIS")
        logger.info("=" * 80)
        logger.info(f"Check Image: {check_image}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 80)
        
        # Build the message for the agent
        message_parts = [
            f"Analyze this check for fraud: {check_image}",
        ]
        
        if comparison_signatures:
            message_parts.append(f"Compare signature against: {', '.join(comparison_signatures)}")
        
        if expected_watermark:
            message_parts.append(f"Expected watermark: {expected_watermark}")
        
        if focus_areas:
            message_parts.append(f"Focus tampering detection on: {', '.join(focus_areas)}")
        
        message = "\n".join(message_parts)
        
        # Prepare the request
        request_data = {
            "message": message,
            "use_tools": True,
            "max_tool_iterations": 5,
            "mock_tools": False,
            "context": {
                "check_image": check_image,
                "comparison_signatures": comparison_signatures or [],
                "expected_watermark": expected_watermark,
                "focus_areas": focus_areas or []
            }
        }
        
        logger.info(f"[ADK_CLIENT] Sending request to ADK server")
        logger.debug(f"[ADK_CLIENT] Request: {json.dumps(request_data, indent=2)}")
        
        try:
            # Call the ADK agent execution endpoint
            url = f"{self.adk_url}/agents/{self.agent_id}/run"
            logger.info(f"[ADK_CLIENT] POST {url}")
            
            response = self.client.post(
                url,
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"[ADK_CLIENT] ✓ Analysis complete")
            logger.info(f"[ADK_CLIENT] Response received: {result.get('success', False)}")
            logger.info(f"[ADK_CLIENT] Tool calls made: {result.get('tool_calls_made', 0)}")
            logger.info(f"[ADK_CLIENT] Duration: {result.get('duration_seconds', 0):.2f}s")
            
            if result.get('usage'):
                logger.info(f"[ADK_CLIENT] Tokens used: {result['usage'].get('total_tokens', 0)}")
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("ANALYSIS RESULTS")
            logger.info("=" * 80)
            logger.info(result.get('response', 'No response'))
            logger.info("=" * 80)
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[ADK_CLIENT] HTTP error: {e}")
            logger.error(f"[ADK_CLIENT] Response: {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "response": "Analysis failed due to server error"
            }
        except Exception as e:
            logger.error(f"[ADK_CLIENT] Error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": "Analysis failed due to client error"
            }
    
    def check_agent_status(self) -> Dict[str, Any]:
        """
        Check if the fraud detection agent exists and is configured.
        
        Returns:
            Agent configuration or error
        """
        try:
            url = f"{self.adk_url}/agents/{self.agent_id}"
            logger.info(f"[ADK_CLIENT] Checking agent status: GET {url}")
            
            response = self.client.get(url)
            response.raise_for_status()
            
            agent_config = response.json()
            logger.info(f"[ADK_CLIENT] ✓ Agent found: {agent_config.get('name', 'Unknown')}")
            logger.info(f"[ADK_CLIENT] Tools configured: {len(agent_config.get('tools', []))}")
            
            return agent_config
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[ADK_CLIENT] Agent not found: {e}")
            return {"error": f"Agent '{self.agent_id}' not found. Please create it first."}
        except Exception as e:
            logger.error(f"[ADK_CLIENT] Error checking agent: {e}")
            return {"error": str(e)}


def setup_agent_if_needed(adk_url: str, agent_id: str) -> bool:
    """
    Setup the fraud detection agent if it doesn't exist.
    
    Returns:
        True if agent exists or was created successfully, False otherwise
    """
    try:
        # Import the setup function
        sys.path.insert(0, str(Path(__file__).parent))
        from setup_fraud_agent import setup_fraud_detection_agent
        
        logger.info("\n" + "=" * 80)
        logger.info("AUTO-SETUP: Deploying Fraud Detection Agent")
        logger.info("=" * 80)
        
        success = setup_fraud_detection_agent(adk_url)
        
        if success:
            logger.info("✓ Agent deployment successful")
            return True
        else:
            logger.error("✗ Agent deployment failed")
            return False
            
    except Exception as e:
        logger.error(f"Error during agent setup: {e}", exc_info=True)
        return False


def main():
    """Main example execution."""
    
    # Configuration
    ADK_URL = os.getenv("ADK_URL", "http://localhost:8100")
    AGENT_ID = os.getenv("FRAUD_AGENT_ID", "fraud-detection-agent")
    
    # Example check images (replace with actual paths)
    CHECK_IMAGE = "data/fraud_detection/sample_checks/check_001.jpg"
    SIGNATURE_SAMPLES = [
        "data/fraud_detection/sample_signatures/sig_001.jpg",
        "data/fraud_detection/sample_signatures/sig_002.jpg",
        "data/fraud_detection/sample_signatures/sig_003.jpg"
    ]
    EXPECTED_WATERMARK = "Bank of America watermark with eagle emblem"
    FOCUS_AREAS = ["amount", "payee", "date", "signature"]
    
    logger.info("Starting ADK Fraud Detection Example")
    logger.info(f"ADK Server: {ADK_URL}")
    logger.info(f"Agent ID: {AGENT_ID}")
    
    # Initialize client
    client = ADKFraudDetectionClient(ADK_URL, AGENT_ID)
    
    # Check if agent exists
    logger.info("\n" + "=" * 80)
    logger.info("CHECKING AGENT STATUS")
    logger.info("=" * 80)
    agent_status = client.check_agent_status()
    
    if "error" in agent_status:
        logger.warning(f"Agent not found: {agent_status['error']}")
        logger.info("Attempting to deploy agent automatically...")
        
        # Try to setup the agent
        if not setup_agent_if_needed(ADK_URL, AGENT_ID):
            logger.error("\nAutomatic agent deployment failed!")
            logger.error("Please run manually: python examples/fraud_detection/setup_fraud_agent.py")
            return
        
        # Verify agent was created
        agent_status = client.check_agent_status()
        if "error" in agent_status:
            logger.error("Agent still not found after setup. Please check ADK server logs.")
            return
    
    # Run analysis
    result = client.analyze_check(
        check_image=CHECK_IMAGE,
        comparison_signatures=SIGNATURE_SAMPLES,
        expected_watermark=EXPECTED_WATERMARK,
        focus_areas=FOCUS_AREAS
    )
    
    # Display final results
    print("\n" + "=" * 80)
    print("FRAUD DETECTION ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Success: {result.get('success', False)}")
    print(f"Agent: {result.get('agent_name', 'Unknown')}")
    print(f"Model: {result.get('model', 'Unknown')}")
    print(f"Duration: {result.get('duration_seconds', 0):.2f}s")
    print(f"Tool Calls: {result.get('tool_calls_made', 0)}")
    
    if result.get('usage'):
        print(f"\nToken Usage:")
        print(f"  Prompt: {result['usage'].get('prompt_tokens', 0)}")
        print(f"  Completion: {result['usage'].get('completion_tokens', 0)}")
        print(f"  Total: {result['usage'].get('total_tokens', 0)}")
    
    print(f"\nAnalysis Response:")
    print("-" * 80)
    print(result.get('response', 'No response'))
    print("=" * 80)
    
    # Save results
    output_file = f"fraud_analysis_adk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to: {output_file}")
    logger.info("Analysis complete!")


if __name__ == "__main__":
    main()
