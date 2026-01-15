"""
Wrapper function for ImageFraudDetector to work with ADK Python tool executor.

This wrapper handles the instantiation of ImageFraudDetector with LLM configuration
and routes to the appropriate method based on the action parameter.
"""

import os
from typing import Dict, Any, List, Optional
from .image_fraud_detector import ImageFraudDetector


def execute_fraud_detection(
    action: str,
    primary_check: str,
    comparison_signatures: Optional[List[str]] = None,
    expected_watermark: Optional[str] = None,
    focus_areas: Optional[List[str]] = None,
    tool_config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute fraud detection analysis.
    
    This wrapper function instantiates ImageFraudDetector with LLM configuration
    and calls the appropriate method based on the action parameter.
    
    Args:
        action: Type of analysis (analyze_signature, detect_watermark, detect_tampering, comprehensive_analysis)
        primary_check: Path to the check image being analyzed
        comparison_signatures: Paths to known valid signature samples
        expected_watermark: Expected watermark description
        focus_areas: Areas to focus tampering detection on
        tool_config: Tool configuration from ADK (contains LLM settings)
        **kwargs: Additional arguments
        
    Returns:
        Analysis results dictionary
    """
    # Get LLM configuration from environment or tool_config
    llm_endpoint = os.getenv("LLM_ENDPOINT", "https://integrate.api.nvidia.com/v1/chat/completions")
    llm_api_key = os.getenv("LLM_API_KEY", "")
    llm_model = os.getenv("LLM_MODEL", "meta/llama-3.2-90b-vision-instruct")
    
    # Ensure endpoint has /chat/completions
    if not llm_endpoint.endswith("/chat/completions"):
        llm_endpoint = f"{llm_endpoint.rstrip('/')}/chat/completions"
    
    # Initialize the detector
    detector = ImageFraudDetector(
        llm_endpoint=llm_endpoint,
        llm_api_key=llm_api_key,
        model=llm_model
    )
    
    # Route to the appropriate method based on action
    if action == "analyze_signature":
        if not comparison_signatures:
            return {"error": "comparison_signatures required for signature analysis"}
        return detector.analyze_signature(primary_check, comparison_signatures)
    
    elif action == "detect_watermark":
        return detector.detect_watermark(primary_check, expected_watermark)
    
    elif action == "detect_tampering":
        return detector.detect_tampering(primary_check, focus_areas)
    
    elif action == "comprehensive_analysis":
        return detector.comprehensive_fraud_analysis(
            primary_check=primary_check,
            comparison_signatures=comparison_signatures,
            expected_watermark=expected_watermark,
            focus_areas=focus_areas
        )
    
    else:
        return {"error": f"Unknown action: {action}"}
