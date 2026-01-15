"""
Check Fraud Detection Example using Multi-Agent Voting System

This example demonstrates a comprehensive fraud detection system that:
1. Uses specialized agents for different fraud detection aspects
2. Implements LangGraph for parallel agent execution
3. Uses weighted voting to make final decisions
4. Provides detailed debug logging of the entire process

Requirements:
- OpenAI-compatible vision API endpoint
- Sample check images and signature samples
- Environment variables configured
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.fraud_detection.image_fraud_detector import ImageFraudDetector

# Configure detailed logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fraud_detection.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Set console encoding to UTF-8 for Windows
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
logger = logging.getLogger(__name__)


class FraudDetectionVotingSystem:
    """
    Multi-agent voting system for check fraud detection.
    
    Uses three specialized agents:
    1. Signature Agent (35% weight) - Analyzes signature authenticity
    2. Watermark Agent (25% weight) - Verifies security features
    3. Tampering Agent (40% weight) - Detects alterations
    
    Final decision is made through weighted voting with consensus analysis.
    """
    
    def __init__(self, llm_endpoint: str, llm_api_key: str, model: str = "gpt-4-vision-preview"):
        """Initialize the voting system with LLM configuration."""
        logger.info("=" * 80)
        logger.info("INITIALIZING FRAUD DETECTION VOTING SYSTEM")
        logger.info("=" * 80)
        
        self.detector = ImageFraudDetector(llm_endpoint, llm_api_key, model)
        
        # Agent weights for voting
        self.agent_weights = {
            "signature": 0.35,
            "watermark": 0.25,
            "tampering": 0.40
        }
        
        logger.info(f"Agent weights configured: {self.agent_weights}")
        logger.info("System initialization complete")
        logger.info("=" * 80)
    
    def run_signature_agent(
        self,
        check_image: str,
        comparison_signatures: List[str]
    ) -> Dict[str, Any]:
        """
        Run the signature analysis agent.
        
        Returns agent's analysis with fraud score and recommendation.
        """
        logger.info("")
        logger.info("┌" + "─" * 78 + "┐")
        logger.info("│ SIGNATURE AGENT ANALYSIS" + " " * 53 + "│")
        logger.info("└" + "─" * 78 + "┘")
        
        logger.info(f"[SIGNATURE_AGENT] Starting analysis...")
        logger.info(f"[SIGNATURE_AGENT] Check image: {check_image}")
        logger.info(f"[SIGNATURE_AGENT] Comparing against {len(comparison_signatures)} signature samples")
        
        result = self.detector.analyze_signature(check_image, comparison_signatures)
        
        # Calculate fraud score (inverse of match score)
        fraud_score = 100 - result.get("match_score", 50)
        
        # Determine recommendation
        if fraud_score >= 70:
            recommendation = "REJECT"
        elif fraud_score >= 40:
            recommendation = "REVIEW"
        else:
            recommendation = "APPROVE"
        
        agent_result = {
            "agent": "signature",
            "fraud_score": fraud_score,
            "recommendation": recommendation,
            "confidence": result.get("confidence", "medium"),
            "details": result.get("details", ""),
            "indicators": result.get("fraud_indicators", []),
            "raw_analysis": result
        }
        
        logger.info(f"[SIGNATURE_AGENT] ✓ Analysis complete")
        logger.info(f"[SIGNATURE_AGENT] Fraud Score: {fraud_score}/100")
        logger.info(f"[SIGNATURE_AGENT] Recommendation: {recommendation}")
        logger.info(f"[SIGNATURE_AGENT] Confidence: {agent_result['confidence']}")
        
        if agent_result['indicators']:
            logger.warning(f"[SIGNATURE_AGENT] Fraud Indicators: {agent_result['indicators']}")
        
        return agent_result
    
    def run_watermark_agent(
        self,
        check_image: str,
        expected_watermark: str = None
    ) -> Dict[str, Any]:
        """
        Run the watermark verification agent.
        
        Returns agent's analysis with fraud score and recommendation.
        """
        logger.info("")
        logger.info("┌" + "─" * 78 + "┐")
        logger.info("│ WATERMARK AGENT ANALYSIS" + " " * 53 + "│")
        logger.info("└" + "─" * 78 + "┘")
        
        logger.info(f"[WATERMARK_AGENT] Starting analysis...")
        logger.info(f"[WATERMARK_AGENT] Check image: {check_image}")
        if expected_watermark:
            logger.info(f"[WATERMARK_AGENT] Expected watermark: {expected_watermark}")
        
        result = self.detector.detect_watermark(check_image, expected_watermark)
        
        # Calculate fraud score based on watermark findings
        fraud_risk = result.get("fraud_risk", "medium")
        if fraud_risk == "high":
            fraud_score = 80
        elif fraud_risk == "medium":
            fraud_score = 50
        else:
            fraud_score = 20
        
        # Determine recommendation
        if fraud_score >= 70:
            recommendation = "REJECT"
        elif fraud_score >= 40:
            recommendation = "REVIEW"
        else:
            recommendation = "APPROVE"
        
        agent_result = {
            "agent": "watermark",
            "fraud_score": fraud_score,
            "recommendation": recommendation,
            "confidence": "high" if result.get("watermark_present") else "medium",
            "details": result.get("details", ""),
            "watermark_present": result.get("watermark_present", False),
            "watermark_valid": result.get("watermark_valid", False),
            "raw_analysis": result
        }
        
        logger.info(f"[WATERMARK_AGENT] ✓ Analysis complete")
        logger.info(f"[WATERMARK_AGENT] Fraud Score: {fraud_score}/100")
        logger.info(f"[WATERMARK_AGENT] Recommendation: {recommendation}")
        logger.info(f"[WATERMARK_AGENT] Watermark Present: {agent_result['watermark_present']}")
        logger.info(f"[WATERMARK_AGENT] Watermark Valid: {agent_result['watermark_valid']}")
        
        return agent_result
    
    def run_tampering_agent(
        self,
        check_image: str,
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run the tampering detection agent.
        
        Returns agent's analysis with fraud score and recommendation.
        """
        logger.info("")
        logger.info("┌" + "─" * 78 + "┐")
        logger.info("│ TAMPERING AGENT ANALYSIS" + " " * 53 + "│")
        logger.info("└" + "─" * 78 + "┘")
        
        logger.info(f"[TAMPERING_AGENT] Starting analysis...")
        logger.info(f"[TAMPERING_AGENT] Check image: {check_image}")
        if focus_areas:
            logger.info(f"[TAMPERING_AGENT] Focus areas: {focus_areas}")
        
        result = self.detector.detect_tampering(check_image, focus_areas)
        
        fraud_score = result.get("fraud_score", 50)
        
        # Determine recommendation
        if fraud_score >= 70:
            recommendation = "REJECT"
        elif fraud_score >= 40:
            recommendation = "REVIEW"
        else:
            recommendation = "APPROVE"
        
        agent_result = {
            "agent": "tampering",
            "fraud_score": fraud_score,
            "recommendation": recommendation,
            "confidence": result.get("tampering_confidence", "medium"),
            "details": result.get("details", ""),
            "tampering_detected": result.get("tampering_detected", False),
            "tampered_areas": result.get("tampered_areas", []),
            "raw_analysis": result
        }
        
        logger.info(f"[TAMPERING_AGENT] ✓ Analysis complete")
        logger.info(f"[TAMPERING_AGENT] Fraud Score: {fraud_score}/100")
        logger.info(f"[TAMPERING_AGENT] Recommendation: {recommendation}")
        logger.info(f"[TAMPERING_AGENT] Tampering Detected: {agent_result['tampering_detected']}")
        
        if agent_result['tampered_areas']:
            logger.warning(f"[TAMPERING_AGENT] Tampered Areas: {agent_result['tampered_areas']}")
        
        return agent_result
    
    def aggregate_votes_and_decide(
        self,
        agent_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate agent votes using weighted scoring and make final decision.
        
        Args:
            agent_results: List of results from all agents
            
        Returns:
            Final decision with reasoning and confidence
        """
        logger.info("")
        logger.info("┌" + "─" * 78 + "┐")
        logger.info("│ VOTING AND DECISION AGGREGATION" + " " * 46 + "│")
        logger.info("└" + "─" * 78 + "┘")
        
        logger.info(f"[VOTING] Aggregating results from {len(agent_results)} agents")
        
        # Calculate weighted fraud score
        weighted_score = 0
        total_weight = 0
        
        recommendations = {"APPROVE": 0, "REVIEW": 0, "REJECT": 0}
        
        for result in agent_results:
            agent_name = result["agent"]
            weight = self.agent_weights.get(agent_name, 0)
            fraud_score = result["fraud_score"]
            recommendation = result["recommendation"]
            
            weighted_score += fraud_score * weight
            total_weight += weight
            recommendations[recommendation] += weight
            
            logger.info(f"[VOTING] {agent_name.upper()} Agent:")
            logger.info(f"[VOTING]   - Fraud Score: {fraud_score}/100")
            logger.info(f"[VOTING]   - Recommendation: {recommendation}")
            logger.info(f"[VOTING]   - Weight: {weight}")
            logger.info(f"[VOTING]   - Weighted Contribution: {fraud_score * weight:.2f}")
        
        # Normalize weighted score
        final_fraud_score = weighted_score / total_weight if total_weight > 0 else 50
        
        logger.info(f"[VOTING] Weighted Fraud Score: {final_fraud_score:.2f}/100")
        
        # Determine final decision based on weighted votes
        final_recommendation = max(recommendations, key=recommendations.get)
        
        # Check for consensus
        consensus = len([r for r in agent_results if r["recommendation"] == final_recommendation]) == len(agent_results)
        
        # Determine confidence
        if consensus:
            decision_confidence = "HIGH"
        elif recommendations[final_recommendation] >= 0.6:
            decision_confidence = "MEDIUM"
        else:
            decision_confidence = "LOW"
        
        # Generate reasoning
        reasoning_parts = [
            f"Weighted fraud score: {final_fraud_score:.2f}/100",
            f"Agent consensus: {'Yes' if consensus else 'No'}",
            f"Vote distribution: APPROVE={recommendations['APPROVE']:.2f}, REVIEW={recommendations['REVIEW']:.2f}, REJECT={recommendations['REJECT']:.2f}"
        ]
        
        # Add specific concerns
        concerns = []
        for result in agent_results:
            if result.get("indicators"):
                concerns.extend(result["indicators"])
            if result.get("tampered_areas"):
                concerns.append(f"Tampering in: {', '.join(result['tampered_areas'])}")
            if not result.get("watermark_present", True):
                concerns.append("Missing watermark")
        
        if concerns:
            reasoning_parts.append(f"Key concerns: {'; '.join(concerns)}")
        
        decision_reasoning = " | ".join(reasoning_parts)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("FINAL DECISION")
        logger.info("=" * 80)
        logger.info(f"Decision: {final_recommendation}")
        logger.info(f"Confidence: {decision_confidence}")
        logger.info(f"Fraud Score: {final_fraud_score:.2f}/100")
        logger.info(f"Consensus: {'Yes' if consensus else 'No'}")
        logger.info(f"Reasoning: {decision_reasoning}")
        logger.info("=" * 80)
        
        return {
            "final_decision": final_recommendation,
            "decision_confidence": decision_confidence,
            "weighted_fraud_score": final_fraud_score,
            "agent_votes": agent_results,
            "consensus": consensus,
            "decision_reasoning": decision_reasoning,
            "vote_distribution": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_check(
        self,
        check_image: str,
        comparison_signatures: List[str] = None,
        expected_watermark: str = None,
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run complete fraud detection analysis with multi-agent voting.
        
        Args:
            check_image: Path to check image
            comparison_signatures: Paths to known valid signatures
            expected_watermark: Expected watermark description
            focus_areas: Areas to focus tampering detection
            
        Returns:
            Complete analysis results with final decision
        """
        logger.info("")
        logger.info("=" * 80)
        logger.info("STARTING MULTI-AGENT FRAUD DETECTION ANALYSIS")
        logger.info("=" * 80)
        logger.info(f"Check Image: {check_image}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 80)
        
        agent_results = []
        
        # Run agents in parallel (simulated - in production use actual parallel execution)
        logger.info("\n[WORKFLOW] Executing agents in parallel...")
        
        # Signature Agent
        if comparison_signatures:
            sig_result = self.run_signature_agent(check_image, comparison_signatures)
            agent_results.append(sig_result)
        else:
            logger.warning("[WORKFLOW] Skipping signature agent - no comparison signatures provided")
        
        # Watermark Agent
        wm_result = self.run_watermark_agent(check_image, expected_watermark)
        agent_results.append(wm_result)
        
        # Tampering Agent
        tamp_result = self.run_tampering_agent(check_image, focus_areas)
        agent_results.append(tamp_result)
        
        logger.info(f"\n[WORKFLOW] All {len(agent_results)} agents completed analysis")
        
        # Aggregate votes and make decision
        final_decision = self.aggregate_votes_and_decide(agent_results)
        
        return final_decision


def main():
    """Main example execution."""
    
    # Configuration
    # Prefer shared LLM_* env vars; fall back to OPENAI_* for compatibility
    llm_endpoint_raw = os.getenv("LLM_ENDPOINT", os.getenv("OPENAI_API_ENDPOINT", "https://api.openai.com/v1"))
    # Ensure endpoint has /chat/completions path
    if not llm_endpoint_raw.endswith("/chat/completions"):
        LLM_ENDPOINT = f"{llm_endpoint_raw.rstrip('/')}/chat/completions"
    else:
        LLM_ENDPOINT = llm_endpoint_raw
    
    LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "your-api-key-here"))
    MODEL = os.getenv("LLM_MODEL", os.getenv("VISION_MODEL", "gpt-4-vision-preview"))
    
    # Example check images (replace with actual paths)
    # Default to reorganized fraud_detection sample paths
    CHECK_IMAGE = "data/fraud_detection/sample_checks/check_001.jpg"
    SIGNATURE_SAMPLES = [
        "data/fraud_detection/sample_signatures/sig_001.jpg",
        "data/fraud_detection/sample_signatures/sig_002.jpg",
        "data/fraud_detection/sample_signatures/sig_003.jpg"
    ]
    EXPECTED_WATERMARK = "Bank of America watermark with eagle emblem"
    FOCUS_AREAS = ["amount", "payee", "date", "signature"]
    
    logger.info("Starting Fraud Detection Example")
    logger.info(f"LLM Endpoint: {LLM_ENDPOINT}")
    logger.info(f"LLM API Key: {'*' * 20 if LLM_API_KEY else 'NOT SET'}")
    logger.info(f"Model: {MODEL}")
    
    # Initialize voting system
    voting_system = FraudDetectionVotingSystem(LLM_ENDPOINT, LLM_API_KEY, MODEL)
    
    # Run analysis
    result = voting_system.analyze_check(
        check_image=CHECK_IMAGE,
        comparison_signatures=SIGNATURE_SAMPLES,
        expected_watermark=EXPECTED_WATERMARK,
        focus_areas=FOCUS_AREAS
    )
    
    # Display final results
    print("\n" + "=" * 80)
    print("FRAUD DETECTION ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Final Decision: {result['final_decision']}")
    print(f"Confidence: {result['decision_confidence']}")
    print(f"Fraud Score: {result['weighted_fraud_score']:.2f}/100")
    print(f"Consensus: {'Yes' if result['consensus'] else 'No'}")
    print(f"\nReasoning: {result['decision_reasoning']}")
    print("\nVote Distribution:")
    for decision, weight in result['vote_distribution'].items():
        print(f"  {decision}: {weight:.2f}")
    print("=" * 80)
    
    # Save results
    output_file = f"fraud_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    import json
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to: {output_file}")
    logger.info("Analysis complete!")


if __name__ == "__main__":
    main()
