"""
Real Vision AI Integration for Image Analysis Tool.

Supports multiple vision AI providers:
- Azure Computer Vision
- AWS Rekognition
- Google Cloud Vision
"""
import os
import logging
from typing import Dict, Any, Optional, List
import base64
import io
from PIL import Image
import httpx

logger = logging.getLogger(__name__)


class VisionAIProvider:
    """Base class for vision AI providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get("provider", "mock")
        
    async def analyze(self, image_bytes: bytes, analysis_type: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image using the configured provider."""
        raise NotImplementedError


class AzureComputerVision(VisionAIProvider):
    """Azure Computer Vision API integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get("azure_endpoint")
        self.api_key = config.get("azure_api_key")
        self.api_version = config.get("azure_api_version", "2023-10-01")
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Azure endpoint and API key are required")
    
    async def analyze(self, image_bytes: bytes, analysis_type: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image using Azure Computer Vision."""
        try:
            if analysis_type == "general":
                return await self._analyze_general(image_bytes, options)
            elif analysis_type == "object_detection":
                return await self._detect_objects(image_bytes, options)
            elif analysis_type == "text_extraction":
                return await self._extract_text(image_bytes, options)
            elif analysis_type == "face_detection":
                return await self._detect_faces(image_bytes, options)
            elif analysis_type == "image_classification":
                return await self._classify_image(image_bytes, options)
            elif analysis_type == "color_analysis":
                return await self._analyze_colors(image_bytes, options)
            elif analysis_type == "quality_assessment":
                return await self._assess_quality(image_bytes, options)
            else:
                return {"error": f"Unknown analysis type: {analysis_type}"}
        except Exception as e:
            logger.error(f"Azure analysis error: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def _analyze_general(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Get general image information using Azure."""
        url = f"{self.endpoint}/vision/v{self.api_version}/analyze"
        
        params = {
            "visualFeatures": "Description,Metadata,ImageType",
            "language": options.get("language", "en")
        }
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/octet-stream"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params, headers=headers, content=image_bytes)
            response.raise_for_status()
            data = response.json()
        
        # Extract image info
        img = Image.open(io.BytesIO(image_bytes))
        
        return {
            "image_format": img.format or "Unknown",
            "color_mode": img.mode,
            "dimensions": {
                "width": data.get("metadata", {}).get("width", img.width),
                "height": data.get("metadata", {}).get("height", img.height)
            },
            "aspect_ratio": round(img.width / img.height, 2) if img.height > 0 else 0,
            "file_size_kb": round(len(image_bytes) / 1024, 2),
            "megapixels": round(img.width * img.height / 1_000_000, 2),
            "description": data.get("description", {}).get("captions", [{}])[0].get("text", ""),
            "tags": [tag["name"] for tag in data.get("description", {}).get("tags", [])],
            "is_clip_art": data.get("imageType", {}).get("clipArtType", 0) > 0,
            "is_line_drawing": data.get("imageType", {}).get("lineDrawingType", 0) > 0
        }
    
    async def _detect_objects(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Detect objects using Azure Computer Vision."""
        url = f"{self.endpoint}/vision/v{self.api_version}/detect"
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/octet-stream"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, content=image_bytes)
            response.raise_for_status()
            data = response.json()
        
        confidence_threshold = options.get("confidence_threshold", 0.5)
        max_objects = options.get("max_objects", 10)
        
        objects = []
        for obj in data.get("objects", []):
            if obj.get("confidence", 0) >= confidence_threshold:
                objects.append({
                    "label": obj.get("object", "unknown"),
                    "confidence": round(obj.get("confidence", 0), 2),
                    "bounding_box": obj.get("rectangle", {})
                })
        
        objects = objects[:max_objects]
        
        return {
            "objects_detected": objects,
            "total_objects": len(objects),
            "confidence_threshold": confidence_threshold,
            "provider": "azure_computer_vision"
        }
    
    async def _extract_text(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text using Azure OCR."""
        url = f"{self.endpoint}/vision/v{self.api_version}/read/analyze"
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/octet-stream"
        }
        
        # Start OCR operation
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, content=image_bytes)
            response.raise_for_status()
            
            # Get operation location
            operation_url = response.headers.get("Operation-Location")
            if not operation_url:
                return {"error": "No operation location returned"}
            
            # Poll for results
            import asyncio
            max_attempts = 10
            for _ in range(max_attempts):
                await asyncio.sleep(1)
                result_response = await client.get(
                    operation_url,
                    headers={"Ocp-Apim-Subscription-Key": self.api_key}
                )
                result_response.raise_for_status()
                result = result_response.json()
                
                if result.get("status") == "succeeded":
                    break
            else:
                return {"error": "OCR operation timed out"}
        
        # Extract text
        text_blocks = []
        full_text = []
        
        for read_result in result.get("analyzeResult", {}).get("readResults", []):
            for line in read_result.get("lines", []):
                text_blocks.append({
                    "text": line.get("text", ""),
                    "confidence": round(sum(word.get("confidence", 0) for word in line.get("words", [])) / max(len(line.get("words", [])), 1), 2),
                    "bounding_box": line.get("boundingBox", [])
                })
                full_text.append(line.get("text", ""))
        
        return {
            "text_blocks": text_blocks,
            "full_text": "\n".join(full_text),
            "total_blocks": len(text_blocks),
            "language": options.get("language", "en"),
            "provider": "azure_computer_vision"
        }
    
    async def _detect_faces(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Detect faces using Azure Face API."""
        # Note: Azure Face API requires a separate endpoint
        face_endpoint = self.config.get("azure_face_endpoint", self.endpoint)
        url = f"{face_endpoint}/face/v1.0/detect"
        
        params = {
            "returnFaceId": "true",
            "returnFaceLandmarks": options.get("return_landmarks", "true"),
            "returnFaceAttributes": "age,gender,emotion,smile,facialHair,glasses,accessories"
        }
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/octet-stream"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params, headers=headers, content=image_bytes)
            response.raise_for_status()
            data = response.json()
        
        faces = []
        for face in data:
            face_info = {
                "face_id": face.get("faceId"),
                "bounding_box": face.get("faceRectangle", {}),
                "attributes": face.get("faceAttributes", {})
            }
            
            if options.get("return_landmarks", True):
                face_info["landmarks"] = face.get("faceLandmarks", {})
            
            faces.append(face_info)
        
        return {
            "faces_detected": faces,
            "total_faces": len(faces),
            "provider": "azure_face_api"
        }
    
    async def _classify_image(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Classify image using Azure Computer Vision."""
        url = f"{self.endpoint}/vision/v{self.api_version}/analyze"
        
        params = {
            "visualFeatures": "Categories,Tags",
            "language": options.get("language", "en")
        }
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/octet-stream"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params, headers=headers, content=image_bytes)
            response.raise_for_status()
            data = response.json()
        
        categories = [
            {
                "name": cat.get("name", ""),
                "confidence": round(cat.get("score", 0), 2)
            }
            for cat in data.get("categories", [])
        ]
        
        tags = [
            {
                "name": tag.get("name", ""),
                "confidence": round(tag.get("confidence", 0), 2)
            }
            for tag in data.get("tags", [])
        ]
        
        return {
            "categories": sorted(categories, key=lambda x: x["confidence"], reverse=True),
            "tags": sorted(tags, key=lambda x: x["confidence"], reverse=True)[:10],
            "primary_category": categories[0]["name"] if categories else "unknown",
            "provider": "azure_computer_vision"
        }
    
    async def _analyze_colors(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze colors using Azure Computer Vision."""
        url = f"{self.endpoint}/vision/v{self.api_version}/analyze"
        
        params = {
            "visualFeatures": "Color"
        }
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/octet-stream"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params, headers=headers, content=image_bytes)
            response.raise_for_status()
            data = response.json()
        
        color_data = data.get("color", {})
        
        return {
            "dominant_color_foreground": color_data.get("dominantColorForeground"),
            "dominant_color_background": color_data.get("dominantColorBackground"),
            "dominant_colors": color_data.get("dominantColors", []),
            "accent_color": color_data.get("accentColor"),
            "is_bw_image": color_data.get("isBwImg", False),
            "provider": "azure_computer_vision"
        }
    
    async def _assess_quality(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Assess image quality using Azure Computer Vision."""
        url = f"{self.endpoint}/vision/v{self.api_version}/analyze"
        
        params = {
            "visualFeatures": "Description,ImageType"
        }
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/octet-stream"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params, headers=headers, content=image_bytes)
            response.raise_for_status()
            data = response.json()
        
        # Basic quality metrics from Azure
        img = Image.open(io.BytesIO(image_bytes))
        
        return {
            "resolution": f"{img.width}x{img.height}",
            "megapixels": round(img.width * img.height / 1_000_000, 2),
            "is_clip_art": data.get("imageType", {}).get("clipArtType", 0) > 0,
            "is_line_drawing": data.get("imageType", {}).get("lineDrawingType", 0) > 0,
            "format": img.format,
            "mode": img.mode,
            "file_size_kb": round(len(image_bytes) / 1024, 2),
            "provider": "azure_computer_vision"
        }


class AWSRekognition(VisionAIProvider):
    """AWS Rekognition integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.region = config.get("aws_region", "us-east-1")
        self.access_key = config.get("aws_access_key_id")
        self.secret_key = config.get("aws_secret_access_key")
        
        if not self.access_key or not self.secret_key:
            raise ValueError("AWS credentials are required")
        
        try:
            import boto3
            self.client = boto3.client(
                'rekognition',
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
        except ImportError:
            raise ImportError("boto3 is required for AWS Rekognition. Install with: pip install boto3")
    
    async def analyze(self, image_bytes: bytes, analysis_type: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image using AWS Rekognition."""
        try:
            if analysis_type == "general":
                return await self._analyze_general(image_bytes, options)
            elif analysis_type == "object_detection":
                return await self._detect_objects(image_bytes, options)
            elif analysis_type == "text_extraction":
                return await self._extract_text(image_bytes, options)
            elif analysis_type == "face_detection":
                return await self._detect_faces(image_bytes, options)
            elif analysis_type == "image_classification":
                return await self._classify_image(image_bytes, options)
            else:
                return {"error": f"Analysis type '{analysis_type}' not supported by AWS Rekognition"}
        except Exception as e:
            logger.error(f"AWS Rekognition error: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def _analyze_general(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Get general image information."""
        img = Image.open(io.BytesIO(image_bytes))
        
        # Get labels for description
        response = self.client.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=10,
            MinConfidence=70
        )
        
        labels = [label['Name'] for label in response.get('Labels', [])]
        
        return {
            "image_format": img.format or "Unknown",
            "color_mode": img.mode,
            "dimensions": {"width": img.width, "height": img.height},
            "aspect_ratio": round(img.width / img.height, 2) if img.height > 0 else 0,
            "file_size_kb": round(len(image_bytes) / 1024, 2),
            "megapixels": round(img.width * img.height / 1_000_000, 2),
            "detected_labels": labels,
            "provider": "aws_rekognition"
        }
    
    async def _detect_objects(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Detect objects using AWS Rekognition."""
        confidence_threshold = options.get("confidence_threshold", 50)
        max_objects = options.get("max_objects", 10)
        
        response = self.client.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=max_objects,
            MinConfidence=confidence_threshold * 100
        )
        
        objects = []
        for label in response.get('Labels', []):
            for instance in label.get('Instances', []):
                objects.append({
                    "label": label['Name'],
                    "confidence": round(instance.get('Confidence', 0) / 100, 2),
                    "bounding_box": instance.get('BoundingBox', {})
                })
        
        return {
            "objects_detected": objects[:max_objects],
            "total_objects": len(objects),
            "confidence_threshold": confidence_threshold,
            "provider": "aws_rekognition"
        }
    
    async def _extract_text(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text using AWS Rekognition."""
        response = self.client.detect_text(Image={'Bytes': image_bytes})
        
        text_blocks = []
        full_text = []
        
        for detection in response.get('TextDetections', []):
            if detection.get('Type') == 'LINE':
                text_blocks.append({
                    "text": detection.get('DetectedText', ''),
                    "confidence": round(detection.get('Confidence', 0) / 100, 2),
                    "bounding_box": detection.get('Geometry', {}).get('BoundingBox', {})
                })
                full_text.append(detection.get('DetectedText', ''))
        
        return {
            "text_blocks": text_blocks,
            "full_text": "\n".join(full_text),
            "total_blocks": len(text_blocks),
            "provider": "aws_rekognition"
        }
    
    async def _detect_faces(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Detect faces using AWS Rekognition."""
        response = self.client.detect_faces(
            Image={'Bytes': image_bytes},
            Attributes=['ALL']
        )
        
        faces = []
        for face in response.get('FaceDetails', []):
            faces.append({
                "bounding_box": face.get('BoundingBox', {}),
                "confidence": round(face.get('Confidence', 0) / 100, 2),
                "attributes": {
                    "age_range": face.get('AgeRange', {}),
                    "gender": face.get('Gender', {}),
                    "emotions": face.get('Emotions', []),
                    "smile": face.get('Smile', {}),
                    "eyeglasses": face.get('Eyeglasses', {}),
                    "sunglasses": face.get('Sunglasses', {}),
                    "beard": face.get('Beard', {}),
                    "mustache": face.get('Mustache', {})
                },
                "landmarks": face.get('Landmarks', []) if options.get("return_landmarks", True) else []
            })
        
        return {
            "faces_detected": faces,
            "total_faces": len(faces),
            "provider": "aws_rekognition"
        }
    
    async def _classify_image(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Classify image using AWS Rekognition."""
        response = self.client.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=20,
            MinConfidence=50
        )
        
        labels = [
            {
                "name": label['Name'],
                "confidence": round(label.get('Confidence', 0) / 100, 2),
                "categories": [parent['Name'] for parent in label.get('Parents', [])]
            }
            for label in response.get('Labels', [])
        ]
        
        return {
            "labels": sorted(labels, key=lambda x: x["confidence"], reverse=True),
            "primary_label": labels[0]["name"] if labels else "unknown",
            "provider": "aws_rekognition"
        }


class GoogleCloudVision(VisionAIProvider):
    """Google Cloud Vision API integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("google_api_key")
        self.project_id = config.get("google_project_id")
        
        if not self.api_key:
            raise ValueError("Google Cloud API key is required")
        
        self.base_url = "https://vision.googleapis.com/v1"
    
    async def analyze(self, image_bytes: bytes, analysis_type: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image using Google Cloud Vision."""
        try:
            if analysis_type == "general":
                return await self._analyze_general(image_bytes, options)
            elif analysis_type == "object_detection":
                return await self._detect_objects(image_bytes, options)
            elif analysis_type == "text_extraction":
                return await self._extract_text(image_bytes, options)
            elif analysis_type == "face_detection":
                return await self._detect_faces(image_bytes, options)
            elif analysis_type == "image_classification":
                return await self._classify_image(image_bytes, options)
            else:
                return {"error": f"Analysis type '{analysis_type}' not supported by Google Cloud Vision"}
        except Exception as e:
            logger.error(f"Google Cloud Vision error: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def _make_request(self, features: List[Dict], image_bytes: bytes) -> Dict:
        """Make request to Google Cloud Vision API."""
        url = f"{self.base_url}/images:annotate"
        
        request_body = {
            "requests": [{
                "image": {
                    "content": base64.b64encode(image_bytes).decode('utf-8')
                },
                "features": features
            }]
        }
        
        params = {"key": self.api_key}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params, json=request_body)
            response.raise_for_status()
            data = response.json()
        
        return data.get("responses", [{}])[0]
    
    async def _analyze_general(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Get general image information."""
        features = [
            {"type": "LABEL_DETECTION", "maxResults": 10},
            {"type": "IMAGE_PROPERTIES"}
        ]
        
        response = await self._make_request(features, image_bytes)
        
        img = Image.open(io.BytesIO(image_bytes))
        labels = [label.get('description', '') for label in response.get('labelAnnotations', [])]
        
        colors = response.get('imagePropertiesAnnotation', {}).get('dominantColors', {}).get('colors', [])
        dominant_color = colors[0].get('color', {}) if colors else {}
        
        return {
            "image_format": img.format or "Unknown",
            "color_mode": img.mode,
            "dimensions": {"width": img.width, "height": img.height},
            "aspect_ratio": round(img.width / img.height, 2) if img.height > 0 else 0,
            "file_size_kb": round(len(image_bytes) / 1024, 2),
            "megapixels": round(img.width * img.height / 1_000_000, 2),
            "detected_labels": labels,
            "dominant_color": dominant_color,
            "provider": "google_cloud_vision"
        }
    
    async def _detect_objects(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Detect objects using Google Cloud Vision."""
        features = [{"type": "OBJECT_LOCALIZATION"}]
        response = await self._make_request(features, image_bytes)
        
        confidence_threshold = options.get("confidence_threshold", 0.5)
        max_objects = options.get("max_objects", 10)
        
        objects = []
        for obj in response.get('localizedObjectAnnotations', []):
            if obj.get('score', 0) >= confidence_threshold:
                objects.append({
                    "label": obj.get('name', 'unknown'),
                    "confidence": round(obj.get('score', 0), 2),
                    "bounding_box": obj.get('boundingPoly', {})
                })
        
        return {
            "objects_detected": objects[:max_objects],
            "total_objects": len(objects),
            "confidence_threshold": confidence_threshold,
            "provider": "google_cloud_vision"
        }
    
    async def _extract_text(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text using Google Cloud Vision."""
        features = [{"type": "TEXT_DETECTION"}]
        response = await self._make_request(features, image_bytes)
        
        text_annotations = response.get('textAnnotations', [])
        
        if not text_annotations:
            return {
                "text_blocks": [],
                "full_text": "",
                "total_blocks": 0,
                "provider": "google_cloud_vision"
            }
        
        # First annotation is the full text
        full_text = text_annotations[0].get('description', '')
        
        # Rest are individual blocks
        text_blocks = [
            {
                "text": ann.get('description', ''),
                "bounding_box": ann.get('boundingPoly', {})
            }
            for ann in text_annotations[1:]
        ]
        
        return {
            "text_blocks": text_blocks,
            "full_text": full_text,
            "total_blocks": len(text_blocks),
            "provider": "google_cloud_vision"
        }
    
    async def _detect_faces(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Detect faces using Google Cloud Vision."""
        features = [{"type": "FACE_DETECTION"}]
        response = await self._make_request(features, image_bytes)
        
        faces = []
        for face in response.get('faceAnnotations', []):
            faces.append({
                "bounding_box": face.get('boundingPoly', {}),
                "confidence": round(face.get('detectionConfidence', 0), 2),
                "attributes": {
                    "joy": face.get('joyLikelihood', 'UNKNOWN'),
                    "sorrow": face.get('sorrowLikelihood', 'UNKNOWN'),
                    "anger": face.get('angerLikelihood', 'UNKNOWN'),
                    "surprise": face.get('surpriseLikelihood', 'UNKNOWN'),
                    "headwear": face.get('headwearLikelihood', 'UNKNOWN'),
                    "blurred": face.get('blurredLikelihood', 'UNKNOWN')
                },
                "landmarks": face.get('landmarks', []) if options.get("return_landmarks", True) else []
            })
        
        return {
            "faces_detected": faces,
            "total_faces": len(faces),
            "provider": "google_cloud_vision"
        }
    
    async def _classify_image(self, image_bytes: bytes, options: Dict[str, Any]) -> Dict[str, Any]:
        """Classify image using Google Cloud Vision."""
        features = [{"type": "LABEL_DETECTION", "maxResults": 20}]
        response = await self._make_request(features, image_bytes)
        
        labels = [
            {
                "name": label.get('description', ''),
                "confidence": round(label.get('score', 0), 2)
            }
            for label in response.get('labelAnnotations', [])
        ]
        
        return {
            "labels": sorted(labels, key=lambda x: x["confidence"], reverse=True),
            "primary_label": labels[0]["name"] if labels else "unknown",
            "provider": "google_cloud_vision"
        }


def get_vision_provider(config: Dict[str, Any]) -> VisionAIProvider:
    """Factory function to get the appropriate vision AI provider."""
    provider = config.get("provider", "mock")
    
    if provider == "azure":
        return AzureComputerVision(config)
    elif provider == "aws":
        return AWSRekognition(config)
    elif provider == "google":
        return GoogleCloudVision(config)
    else:
        raise ValueError(f"Unknown vision AI provider: {provider}")
