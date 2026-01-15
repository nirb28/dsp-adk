"""
Image Fraud Detection Tool for Check Analysis

This tool performs comprehensive image comparison and fraud detection analysis
for checks and financial documents. It supports:
- Signature comparison across multiple samples
- Watermark detection and verification
- Image tampering detection
- Visual anomaly detection
- Multi-image comparison with detailed scoring
"""

import base64
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


class ImageFraudDetector:
    """
    Comprehensive image fraud detection tool for check analysis.
    
    Supports multiple fraud detection techniques:
    1. Signature comparison - Compare signatures across checks
    2. Watermark verification - Detect and validate watermarks
    3. Tampering detection - Identify image manipulation
    4. Visual anomaly detection - Find suspicious patterns
    """
    
    def __init__(self, llm_endpoint: str, llm_api_key: str, model: str = "gpt-4-vision-preview"):
        """
        Initialize the fraud detector with LLM vision capabilities.
        
        Args:
            llm_endpoint: OpenAI-compatible vision API endpoint
            llm_api_key: API key for authentication
            model: Vision model to use (default: gpt-4-vision-preview)
        """
        self.llm_endpoint = llm_endpoint
        self.llm_api_key = llm_api_key
        self.model = model
        logger.info(f"[INIT] ImageFraudDetector initialized with model: {model}")
    
    def encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        logger.debug(f"[ENCODE] Encoding image: {image_path}")
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
        logger.debug(f"[ENCODE] Successfully encoded image: {len(encoded)} bytes")
        return encoded
    
    def analyze_signature(
        self,
        primary_check_image: str,
        comparison_signatures: List[str],
        analysis_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare signature on primary check against known signature samples.
        
        Args:
            primary_check_image: Path to the check image being analyzed
            comparison_signatures: List of paths to known valid signature samples
            analysis_prompt: Custom analysis prompt (optional)
            
        Returns:
            Dictionary containing:
            - match_score: Overall signature match score (0-100)
            - individual_scores: Scores for each comparison
            - fraud_indicators: List of suspicious findings
            - confidence: Confidence level of the analysis
            - details: Detailed analysis text
        """
        logger.info(f"[SIGNATURE_ANALYSIS] Starting signature analysis")
        logger.info(f"[SIGNATURE_ANALYSIS] Primary check: {primary_check_image}")
        logger.info(f"[SIGNATURE_ANALYSIS] Comparing against {len(comparison_signatures)} signature samples")
        
        if not analysis_prompt:
            analysis_prompt = """
            Analyze the signature on the primary check image and compare it with the provided signature samples.
            
            Focus on:
            1. Stroke patterns and pen pressure
            2. Letter formation and spacing
            3. Overall signature flow and rhythm
            4. Size and proportions
            5. Any signs of tracing or forgery
            
            Provide:
            - Overall match score (0-100) where 100 is perfect match
            - Individual comparison scores for each sample
            - Specific fraud indicators if any
            - Confidence level (low/medium/high)
            - Detailed reasoning
            
            Return response in JSON format:
            {
                "match_score": <0-100>,
                "individual_scores": [<score1>, <score2>, ...],
                "fraud_indicators": ["indicator1", "indicator2", ...],
                "confidence": "low|medium|high",
                "details": "detailed analysis text"
            }
            """
        
        try:
            primary_encoded = self.encode_image(primary_check_image)
            comparison_encoded = [self.encode_image(sig) for sig in comparison_signatures]
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{primary_encoded}"
                            }
                        }
                    ]
                }
            ]
            
            for idx, comp_img in enumerate(comparison_encoded):
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{comp_img}"
                    }
                })
                logger.debug(f"[SIGNATURE_ANALYSIS] Added comparison signature {idx + 1}")
            
            logger.info(f"[SIGNATURE_ANALYSIS] Sending request to LLM vision API")
            response = self._call_vision_api(messages)
            
            result = self._parse_json_response(response)
            logger.info(f"[SIGNATURE_ANALYSIS] Analysis complete - Match Score: {result.get('match_score', 'N/A')}")
            logger.info(f"[SIGNATURE_ANALYSIS] Confidence: {result.get('confidence', 'N/A')}")
            
            if result.get('fraud_indicators'):
                logger.warning(f"[SIGNATURE_ANALYSIS] Fraud indicators detected: {result['fraud_indicators']}")
            
            return result
            
        except Exception as e:
            logger.error(f"[SIGNATURE_ANALYSIS] Error during analysis: {str(e)}")
            return {
                "match_score": 0,
                "individual_scores": [],
                "fraud_indicators": [f"Analysis error: {str(e)}"],
                "confidence": "low",
                "details": f"Error occurred during analysis: {str(e)}"
            }
    
    def detect_watermark(
        self,
        check_image: str,
        expected_watermark_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect and verify watermark presence on check.
        
        Args:
            check_image: Path to the check image
            expected_watermark_description: Description of expected watermark (optional)
            
        Returns:
            Dictionary containing:
            - watermark_present: Boolean indicating watermark presence
            - watermark_valid: Boolean indicating if watermark matches expected
            - watermark_description: Description of detected watermark
            - fraud_risk: Risk level (low/medium/high)
            - details: Detailed analysis
        """
        logger.info(f"[WATERMARK_DETECTION] Starting watermark analysis")
        logger.info(f"[WATERMARK_DETECTION] Check image: {check_image}")
        
        prompt = f"""
        Analyze this check image for watermark presence and authenticity.
        
        Look for:
        1. Visible or subtle watermark patterns
        2. Security features embedded in the paper
        3. Microprinting or special ink patterns
        4. Any signs of watermark tampering or removal
        
        {f"Expected watermark: {expected_watermark_description}" if expected_watermark_description else ""}
        
        Provide analysis in JSON format:
        {{
            "watermark_present": true/false,
            "watermark_valid": true/false,
            "watermark_description": "description of detected watermark",
            "fraud_risk": "low|medium|high",
            "details": "detailed analysis"
        }}
        """
        
        try:
            encoded_image = self.encode_image(check_image)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }
                        }
                    ]
                }
            ]
            
            logger.info(f"[WATERMARK_DETECTION] Sending request to LLM vision API")
            response = self._call_vision_api(messages)
            result = self._parse_json_response(response)
            
            logger.info(f"[WATERMARK_DETECTION] Watermark present: {result.get('watermark_present', 'N/A')}")
            logger.info(f"[WATERMARK_DETECTION] Fraud risk: {result.get('fraud_risk', 'N/A')}")
            
            if result.get('fraud_risk') in ['medium', 'high']:
                logger.warning(f"[WATERMARK_DETECTION] Elevated fraud risk detected!")
            
            return result
            
        except Exception as e:
            logger.error(f"[WATERMARK_DETECTION] Error during analysis: {str(e)}")
            return {
                "watermark_present": False,
                "watermark_valid": False,
                "watermark_description": "Analysis failed",
                "fraud_risk": "high",
                "details": f"Error: {str(e)}"
            }
    
    def detect_tampering(
        self,
        check_image: str,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect signs of image tampering or alteration.
        
        Args:
            check_image: Path to the check image
            focus_areas: Specific areas to focus on (e.g., ["amount", "payee", "date"])
            
        Returns:
            Dictionary containing:
            - tampering_detected: Boolean indicating tampering
            - tampered_areas: List of suspected tampered areas
            - tampering_confidence: Confidence level
            - fraud_score: Overall fraud score (0-100)
            - details: Detailed findings
        """
        logger.info(f"[TAMPERING_DETECTION] Starting tampering analysis")
        logger.info(f"[TAMPERING_DETECTION] Check image: {check_image}")
        if focus_areas:
            logger.info(f"[TAMPERING_DETECTION] Focus areas: {focus_areas}")
        
        focus_text = ""
        if focus_areas:
            focus_text = f"\nPay special attention to these areas: {', '.join(focus_areas)}"
        
        prompt = f"""
        Analyze this check image for signs of tampering or alteration.
        
        Look for:
        1. Inconsistent fonts or handwriting
        2. Erasure marks or correction fluid
        3. Misaligned text or numbers
        4. Different ink colors or pen types
        5. Digital manipulation artifacts
        6. Overwriting or alterations
        {focus_text}
        
        Provide analysis in JSON format:
        {{
            "tampering_detected": true/false,
            "tampered_areas": ["area1", "area2", ...],
            "tampering_confidence": "low|medium|high",
            "fraud_score": <0-100>,
            "details": "detailed findings"
        }}
        """
        
        try:
            encoded_image = self.encode_image(check_image)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }
                        }
                    ]
                }
            ]
            
            logger.info(f"[TAMPERING_DETECTION] Sending request to LLM vision API")
            response = self._call_vision_api(messages)
            result = self._parse_json_response(response)
            
            logger.info(f"[TAMPERING_DETECTION] Tampering detected: {result.get('tampering_detected', 'N/A')}")
            logger.info(f"[TAMPERING_DETECTION] Fraud score: {result.get('fraud_score', 'N/A')}/100")
            
            if result.get('tampering_detected'):
                logger.warning(f"[TAMPERING_DETECTION] Tampered areas: {result.get('tampered_areas', [])}")
            
            return result
            
        except Exception as e:
            logger.error(f"[TAMPERING_DETECTION] Error during analysis: {str(e)}")
            return {
                "tampering_detected": True,
                "tampered_areas": ["unknown"],
                "tampering_confidence": "low",
                "fraud_score": 50,
                "details": f"Error: {str(e)}"
            }
    
    def comprehensive_fraud_analysis(
        self,
        primary_check: str,
        comparison_signatures: Optional[List[str]] = None,
        expected_watermark: Optional[str] = None,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive fraud analysis combining all detection methods.
        
        Args:
            primary_check: Path to the check being analyzed
            comparison_signatures: Paths to known valid signatures
            expected_watermark: Description of expected watermark
            focus_areas: Areas to focus tampering detection on
            
        Returns:
            Dictionary containing:
            - overall_fraud_score: Combined fraud score (0-100)
            - risk_level: Overall risk assessment
            - signature_analysis: Signature comparison results
            - watermark_analysis: Watermark detection results
            - tampering_analysis: Tampering detection results
            - recommendations: List of recommended actions
            - summary: Executive summary of findings
        """
        logger.info(f"[COMPREHENSIVE_ANALYSIS] ========================================")
        logger.info(f"[COMPREHENSIVE_ANALYSIS] Starting comprehensive fraud analysis")
        logger.info(f"[COMPREHENSIVE_ANALYSIS] Check: {primary_check}")
        logger.info(f"[COMPREHENSIVE_ANALYSIS] ========================================")
        
        results = {
            "signature_analysis": None,
            "watermark_analysis": None,
            "tampering_analysis": None
        }
        
        if comparison_signatures:
            logger.info(f"[COMPREHENSIVE_ANALYSIS] Running signature analysis...")
            results["signature_analysis"] = self.analyze_signature(
                primary_check, comparison_signatures
            )
        
        logger.info(f"[COMPREHENSIVE_ANALYSIS] Running watermark detection...")
        results["watermark_analysis"] = self.detect_watermark(
            primary_check, expected_watermark
        )
        
        logger.info(f"[COMPREHENSIVE_ANALYSIS] Running tampering detection...")
        results["tampering_analysis"] = self.detect_tampering(
            primary_check, focus_areas
        )
        
        fraud_score = self._calculate_overall_fraud_score(results)
        risk_level = self._determine_risk_level(fraud_score)
        recommendations = self._generate_recommendations(results, fraud_score)
        summary = self._generate_summary(results, fraud_score, risk_level)
        
        logger.info(f"[COMPREHENSIVE_ANALYSIS] ========================================")
        logger.info(f"[COMPREHENSIVE_ANALYSIS] Analysis complete!")
        logger.info(f"[COMPREHENSIVE_ANALYSIS] Overall fraud score: {fraud_score}/100")
        logger.info(f"[COMPREHENSIVE_ANALYSIS] Risk level: {risk_level}")
        logger.info(f"[COMPREHENSIVE_ANALYSIS] ========================================")
        
        return {
            "overall_fraud_score": fraud_score,
            "risk_level": risk_level,
            "signature_analysis": results["signature_analysis"],
            "watermark_analysis": results["watermark_analysis"],
            "tampering_analysis": results["tampering_analysis"],
            "recommendations": recommendations,
            "summary": summary
        }
    
    def _call_vision_api(self, messages: List[Dict[str, Any]]) -> str:
        """Call the vision API and return response text."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llm_api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000
        }
        
        response = requests.post(
            self.llm_endpoint,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        # Log error details if request fails
        if response.status_code != 200:
            logger.error(f"API Error {response.status_code}: {response.text}")
        
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        try:
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            return json.loads(response_text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            return {"error": "Failed to parse response", "raw_response": response_text}
    
    def _calculate_overall_fraud_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall fraud score from individual analyses."""
        scores = []
        
        if results.get("signature_analysis"):
            sig_score = 100 - results["signature_analysis"].get("match_score", 50)
            scores.append(sig_score)
            logger.debug(f"[SCORE_CALC] Signature fraud component: {sig_score}")
        
        if results.get("watermark_analysis"):
            watermark = results["watermark_analysis"]
            if watermark.get("fraud_risk") == "high":
                scores.append(80)
                logger.debug(f"[SCORE_CALC] Watermark fraud component: 80 (high risk)")
            elif watermark.get("fraud_risk") == "medium":
                scores.append(50)
                logger.debug(f"[SCORE_CALC] Watermark fraud component: 50 (medium risk)")
            else:
                scores.append(20)
                logger.debug(f"[SCORE_CALC] Watermark fraud component: 20 (low risk)")
        
        if results.get("tampering_analysis"):
            tamp_score = results["tampering_analysis"].get("fraud_score", 50)
            scores.append(tamp_score)
            logger.debug(f"[SCORE_CALC] Tampering fraud component: {tamp_score}")
        
        overall = int(sum(scores) / len(scores)) if scores else 50
        logger.info(f"[SCORE_CALC] Overall fraud score calculated: {overall}/100")
        return overall
    
    def _determine_risk_level(self, fraud_score: int) -> str:
        """Determine risk level from fraud score."""
        if fraud_score >= 70:
            level = "HIGH"
        elif fraud_score >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"
        
        logger.info(f"[RISK_ASSESSMENT] Risk level determined: {level}")
        return level
    
    def _generate_recommendations(self, results: Dict[str, Any], fraud_score: int) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        if fraud_score >= 70:
            recommendations.append("REJECT: High fraud risk detected - do not process this check")
            logger.warning(f"[RECOMMENDATIONS] Critical: Check rejection recommended")
        elif fraud_score >= 40:
            recommendations.append("REVIEW: Manual review required before processing")
            logger.info(f"[RECOMMENDATIONS] Manual review recommended")
        else:
            recommendations.append("APPROVE: Low fraud risk - may proceed with standard verification")
            logger.info(f"[RECOMMENDATIONS] Approval recommended with standard verification")
        
        if results.get("signature_analysis"):
            sig = results["signature_analysis"]
            if sig.get("match_score", 0) < 60:
                recommendations.append("Signature verification: Contact account holder for verification")
                logger.info(f"[RECOMMENDATIONS] Signature verification needed")
        
        if results.get("watermark_analysis"):
            wm = results["watermark_analysis"]
            if not wm.get("watermark_present"):
                recommendations.append("Watermark missing: Verify check authenticity with issuing bank")
                logger.info(f"[RECOMMENDATIONS] Watermark verification needed")
        
        if results.get("tampering_analysis"):
            tamp = results["tampering_analysis"]
            if tamp.get("tampering_detected"):
                recommendations.append(f"Tampering detected in: {', '.join(tamp.get('tampered_areas', []))}")
                logger.warning(f"[RECOMMENDATIONS] Tampering investigation required")
        
        return recommendations
    
    def _generate_summary(self, results: Dict[str, Any], fraud_score: int, risk_level: str) -> str:
        """Generate executive summary of findings."""
        summary_parts = [
            f"Fraud Analysis Summary - Risk Level: {risk_level} (Score: {fraud_score}/100)"
        ]
        
        if results.get("signature_analysis"):
            sig = results["signature_analysis"]
            summary_parts.append(
                f"Signature Match: {sig.get('match_score', 0)}% "
                f"(Confidence: {sig.get('confidence', 'unknown')})"
            )
        
        if results.get("watermark_analysis"):
            wm = results["watermark_analysis"]
            summary_parts.append(
                f"Watermark: {'Present' if wm.get('watermark_present') else 'Missing'} "
                f"(Risk: {wm.get('fraud_risk', 'unknown')})"
            )
        
        if results.get("tampering_analysis"):
            tamp = results["tampering_analysis"]
            summary_parts.append(
                f"Tampering: {'Detected' if tamp.get('tampering_detected') else 'Not detected'} "
                f"(Confidence: {tamp.get('tampering_confidence', 'unknown')})"
            )
        
        summary = " | ".join(summary_parts)
        logger.info(f"[SUMMARY] {summary}")
        return summary


def create_tool_config() -> Dict[str, Any]:
    """
    Create ADK tool configuration for the Image Fraud Detector.
    
    Returns:
        Tool configuration dictionary compatible with ADK
    """
    return {
        "name": "image_fraud_detector",
        "type": "python",
        "description": "Comprehensive image fraud detection tool for check analysis. Performs signature comparison, watermark verification, and tampering detection.",
        "python_function": "tools.image_fraud_detector.ImageFraudDetector",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["analyze_signature", "detect_watermark", "detect_tampering", "comprehensive_analysis"],
                    "description": "Type of fraud analysis to perform"
                },
                "primary_check": {
                    "type": "string",
                    "description": "Path to the primary check image being analyzed"
                },
                "comparison_signatures": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Paths to known valid signature samples for comparison"
                },
                "expected_watermark": {
                    "type": "string",
                    "description": "Description of expected watermark on the check"
                },
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific areas to focus tampering detection on (e.g., amount, payee, date)"
                }
            },
            "required": ["action", "primary_check"]
        }
    }
