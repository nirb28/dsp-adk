"""
Setup Fraud Detection Agent in ADK

This script creates the necessary tool and agent configurations in ADK
for fraud detection analysis.
"""

import os
import sys
import json
import httpx
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_fraud_detection_agent(adk_url: str = "http://localhost:8100"):
    """
    Create fraud detection tool and agent in ADK.
    
    Args:
        adk_url: Base URL of the ADK server
    """
    client = httpx.Client(timeout=30.0)
    adk_url = adk_url.rstrip('/')
    
    try:
        # 1. Create the fraud detection tool
        logger.info("=" * 80)
        logger.info("STEP 1: Creating Fraud Detection Tool")
        logger.info("=" * 80)
        
        tool_config = {
            "id": "image_fraud_detector",
            "name": "Image Fraud Detector",
            "description": "Comprehensive image fraud detection tool for check analysis. Performs signature comparison, watermark verification, and tampering detection using vision AI.",
            "tool_type": "python",
            "implementation": {
                "module": "tools.fraud_detection.fraud_detector_wrapper",
                "function": "execute_fraud_detection"
            },
            "parameters": [
                {
                    "name": "action",
                    "type": "string",
                    "description": "Type of fraud analysis to perform",
                    "required": True,
                    "enum": ["analyze_signature", "detect_watermark", "detect_tampering", "comprehensive_analysis"]
                },
                {
                    "name": "primary_check",
                    "type": "string",
                    "description": "Path to the primary check image being analyzed",
                    "required": True
                },
                {
                    "name": "comparison_signatures",
                    "type": "array",
                    "description": "Paths to known valid signature samples for comparison",
                    "required": False,
                    "items": {"type": "string"}
                },
                {
                    "name": "expected_watermark",
                    "type": "string",
                    "description": "Description of expected watermark on the check",
                    "required": False
                },
                {
                    "name": "focus_areas",
                    "type": "array",
                    "description": "Specific areas to focus tampering detection on (e.g., amount, payee, date)",
                    "required": False,
                    "items": {"type": "string"}
                }
            ],
            "usage_instructions": "Use this tool to analyze checks for fraud. For signature analysis, provide comparison_signatures. For comprehensive analysis, provide all optional parameters.",
            "jwt_required": False
        }
        
        # Check if tool already exists
        try:
            response = client.get(f"{adk_url}/tools/image_fraud_detector")
            if response.status_code == 200:
                logger.info("✓ Tool 'image_fraud_detector' already exists")
                # Update it
                response = client.put(f"{adk_url}/tools/image_fraud_detector", json=tool_config)
                response.raise_for_status()
                logger.info("✓ Tool updated successfully")
            else:
                raise Exception("Tool doesn't exist")
        except:
            # Create new tool
            response = client.post(f"{adk_url}/tools", json=tool_config)
            response.raise_for_status()
            logger.info("✓ Tool created successfully")
        
        # 2. Create the fraud detection agent
        logger.info("")
        logger.info("=" * 80)
        logger.info("STEP 2: Creating Fraud Detection Agent")
        logger.info("=" * 80)
        
        # Get LLM configuration from environment
        llm_model = os.getenv("LLM_MODEL", "meta/llama-3.2-90b-vision-instruct")
        llm_endpoint = os.getenv("LLM_ENDPOINT", "https://integrate.api.nvidia.com/v1")
        llm_api_key = os.getenv("LLM_API_KEY", "")
        
        # Ensure endpoint has /chat/completions
        if not llm_endpoint.endswith("/chat/completions"):
            llm_endpoint = f"{llm_endpoint.rstrip('/')}/chat/completions"
        
        agent_config = {
            "id": "fraud-detection-agent",
            "name": "Fraud Detection Agent",
            "description": "AI agent specialized in analyzing checks for fraud using vision AI and multiple detection techniques",
            "system_prompt": """You are a fraud detection specialist analyzing checks for potential fraud.

You have access to image fraud detection tools that can:
1. Analyze signatures and compare them with known valid signatures
2. Detect and verify watermarks on checks
3. Identify signs of tampering or alteration

When analyzing a check:
1. Use the comprehensive_analysis action for complete fraud assessment
2. Provide detailed findings about signature matches, watermark presence, and tampering indicators
3. Give a clear recommendation: APPROVE, REVIEW, or REJECT
4. Explain your reasoning based on the tool results

Be thorough and precise in your analysis.""",
            "llm": {
                "provider": "openai_compatible",
                "model": llm_model,
                "endpoint": llm_endpoint,
                "api_key": llm_api_key,
                "temperature": 0.1,
                "max_tokens": 2000
            },
            "tools": ["image_fraud_detector"],
            "tool_configs": {},
            "jwt_required": False
        }
        
        # Check if agent already exists
        try:
            response = client.get(f"{adk_url}/agents/fraud-detection-agent")
            if response.status_code == 200:
                logger.info("✓ Agent 'fraud-detection-agent' already exists")
                # Update it
                response = client.put(f"{adk_url}/agents/fraud-detection-agent", json=agent_config)
                response.raise_for_status()
                logger.info("✓ Agent updated successfully")
            else:
                raise Exception("Agent doesn't exist")
        except:
            # Create new agent
            response = client.post(f"{adk_url}/agents", json=agent_config)
            response.raise_for_status()
            logger.info("✓ Agent created successfully")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("SETUP COMPLETE!")
        logger.info("=" * 80)
        logger.info("✓ Tool: image_fraud_detector")
        logger.info("✓ Agent: fraud-detection-agent")
        logger.info(f"✓ Model: {llm_model}")
        logger.info(f"✓ Endpoint: {llm_endpoint}")
        logger.info("")
        logger.info("You can now run: python examples/fraud_detection/fraud_detection_adk_example.py")
        logger.info("=" * 80)
        
        return True
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP Error: {e}")
        logger.error(f"Response: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return False
    finally:
        client.close()


if __name__ == "__main__":
    adk_url = os.getenv("ADK_URL", "http://localhost:8100")
    
    logger.info("Fraud Detection Agent Setup")
    logger.info(f"ADK Server: {adk_url}")
    logger.info("")
    
    # Check if ADK server is running
    try:
        client = httpx.Client(timeout=5.0)
        response = client.get(f"{adk_url}/health")
        client.close()
        logger.info("✓ ADK server is running")
        logger.info("")
    except:
        logger.error("✗ ADK server is not running!")
        logger.error(f"Please start the ADK server first: python run.py")
        sys.exit(1)
    
    success = setup_fraud_detection_agent(adk_url)
    sys.exit(0 if success else 1)
