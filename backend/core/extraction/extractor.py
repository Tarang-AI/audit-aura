"""
Compliance Control Extractor
Extracts compliance controls from PDF documents and URLs
"""
import logging
import io
import re
from typing import List, Dict, Any, Optional
import requests
from pypdf import PdfReader
import pdfplumber
from openai import OpenAI

logger = logging.getLogger(__name__)


class ComplianceExtractor:
    """Extract compliance controls from various sources"""
    
    def __init__(self, openai_api_key: str = None, openai_enabled: bool = False,
                 lm_studio_host: str = "http://localhost:1234",
                 lm_studio_model: str = "google/gemma-2-9b", lm_studio_enabled: bool = False,
                 ollama_host: str = "http://ollama:11434",
                 ollama_model: str = "phi4-mini", ollama_enabled: bool = False,
                 opencode_api_key: str = None, opencode_model: str = "minimax-2.5-free",
                 opencode_base_url: str = "https://api.opencode.ai/v1", opencode_enabled: bool = False,
                 anthropic_api_key: str = None, anthropic_model: str = "minimax-m2.5-free",
                 anthropic_base_url: str = "https://opencode.ai/zen", anthropic_enabled: bool = True):
        self.openai_enabled = openai_enabled
        self.client = OpenAI(api_key=openai_api_key) if (openai_enabled and openai_api_key) else None
        
        self.opencode_enabled = opencode_enabled
        self.opencode_api_key = opencode_api_key
        self.opencode_model = opencode_model
        self.opencode_base_url = opencode_base_url
        self.opencode_client = OpenAI(api_key=opencode_api_key, base_url=opencode_base_url) if (opencode_enabled and opencode_api_key) else None

        self.anthropic_enabled = anthropic_enabled
        self.anthropic_api_key = anthropic_api_key
        self.anthropic_model = anthropic_model
        self.anthropic_base_url = anthropic_base_url
        if anthropic_enabled and anthropic_api_key:
            from anthropic import Anthropic
            self.anthropic_client = Anthropic(api_key=anthropic_api_key, base_url=anthropic_base_url)
        else:
            self.anthropic_client = None

        self.lm_studio_host = lm_studio_host
        self.lm_studio_model = lm_studio_model
        self.lm_studio_enabled = lm_studio_enabled
        self.lm_studio_available = self._check_lm_studio() if lm_studio_enabled else False
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model
        self.ollama_enabled = ollama_enabled
        self.ollama_available = self._check_ollama() if ollama_enabled else False
        
        enabled_methods = sum([
            self.lm_studio_enabled,
            self.openai_enabled,
            self.ollama_enabled,
            self.opencode_enabled,
            self.anthropic_enabled
        ])

        if enabled_methods == 0:
            raise ValueError("At least one extraction method must be enabled (ANTHROPIC_ENABLED, OPENCODE_ENABLED, LM_STUDIO_ENABLED, OPENAI_ENABLED, or OLLAMA_ENABLED)")
        
        # Log which extraction method will be used
        if self.anthropic_enabled and self.anthropic_client:
            logger.info(f"Using OpenCode Zen Anthropic-Compatible for extraction ({self.anthropic_model})")
        elif self.opencode_enabled and self.opencode_client:
            logger.info(f"Using OpenCode Zen for extraction ({self.opencode_model})")
        elif self.lm_studio_enabled and self.lm_studio_available:
            logger.info(f"Using LM Studio for extraction ({self.lm_studio_model})")
        elif self.ollama_enabled and self.ollama_available:
            logger.info(f"Using Ollama for extraction ({self.ollama_model})")
        elif self.openai_enabled and self.client:
            logger.info("Using OpenAI for extraction")
        elif self.anthropic_enabled and not self.anthropic_client:
            raise ValueError("Anthropic/OpenCode Zen is enabled but API key is not configured")
        elif self.opencode_enabled and not self.opencode_client:
            raise ValueError("OpenCode Zen is enabled but API key is not configured")
        elif self.lm_studio_enabled and not self.lm_studio_available:
            raise ValueError("LM Studio is enabled but not available. Please start LM Studio or disable it.")
        elif self.ollama_enabled and not self.ollama_available:
            raise ValueError("Ollama is enabled but not available. Please start Ollama or disable it.")
        elif self.openai_enabled and not self.client:
            raise ValueError("OpenAI is enabled but API key is not configured")
        self.extraction_prompt = """
You are a cybersecurity compliance control extraction engine.
Extract all compliance controls found in the text.
Return ONLY valid JSON.

Rules:
- No markdown
- No explanations
- No commentary
- No prose outside JSON
- Output must be parseable with json.loads()

If no controls exist, return:
{{"controls":[]}}

Required schema:

{{
  "controls": [
    {{
      "control_id": "SOC2-CC6.1",
      "description": "Clear control description",
      "condition": "event.field == value",
      "severity": "critical",
      "remediation": "Specific remediation action",
      "category": "Access Control",
      "standard": "SOC2",
      "control_type": "preventive",
      "evidence_required": "Audit evidence",
      "automatable": true
    }}
  ]
}}

- control_id:
  MUST extract the EXACT control ID from the document (e.g., CC1.1, C5-01, ISO-A.5.1).
  DO NOT use generic "001" or similar if a real ID exists.
  If no ID exists, generate a descriptive one: [STANDARD]-[ABBREVIATED-CATEGORY]-[NUMBER].

- description:
  Provide a COMPREHENSIVE and CLEAR description of the control requirement.
  Include context from the document.
  DO NOT use placeholders like "001".

- condition:
  Must be machine-readable.
  Allowed patterns:
    event.field == value
    event.field != value
    exists(event.field)
    not exists(event.field)
    event.field >= value
    event.field <= value

- category:
  Identify the specific compliance category (e.g., Access Control, Encryption, Network Security).

- standard:
  Identify the audit standard (e.g., SOC2, ISO27001, C5, GDPR).

- severity:
  Must be one of: critical, high, medium, low.

- control_type:
  Must be one of:
    preventive
    detective
    corrective

- automatable:
  Must be true or false

- Keep descriptions concise.
- Keep remediation concise.
- Avoid duplicate controls.
- Do not invent unsupported controls.
- Preserve security intent.

Text:
{text}
"""
    
    def _extract_with_anthropic(self, text: str) -> List[Dict[str, Any]]:
        """Extract controls using Anthropic/OpenCode Zen Anthropic-Compatible"""
        try:
            import json
            prompt = self.extraction_prompt.format(text=text)
            
            response = self.anthropic_client.messages.create(
                model=self.anthropic_model,
                max_tokens=2000,
                temperature=0,
                system="You are a compliance expert that extracts controls from audit documents. Always respond with valid JSON objects containing a 'controls' array.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = response.content[0].text
            if not content:
                return []
            
            # Clean markdown if present
            cleaned = re.sub(r'```(?:json)?|```', '', content).strip()
            
            # Extract JSON object safely
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end + 1]
            
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and 'controls' in parsed:
                return parsed['controls']
            elif isinstance(parsed, list):
                return parsed
            return []
        except Exception as e:
            logger.error(f"Anthropic extraction failed: {e}")
            return []

    def _extract_with_opencode(self, text: str) -> List[Dict[str, Any]]:
        """Extract controls using OpenCode Zen"""
        try:
            import json
            prompt = self.extraction_prompt.format(text=text)
            response = self.opencode_client.chat.completions.create(
                model=self.opencode_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a compliance expert that extracts controls from audit documents. Always respond with valid JSON objects containing a 'controls' array."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                return []
            
            parsed = json.loads(content.strip())
            if isinstance(parsed, dict) and 'controls' in parsed:
                return parsed['controls']
            elif isinstance(parsed, list):
                return parsed
            return []
        except Exception as e:
            logger.error(f"OpenCode extraction failed: {e}")
            return []

    def _extract_with_openai(self, text: str) -> List[Dict[str, Any]]:
        """Extract controls using OpenAI"""
        try:
            import json
            prompt = self.extraction_prompt.format(text=text)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a compliance expert that extracts controls from audit documents. Always respond with valid JSON objects containing a 'controls' array."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                return []
            
            parsed = json.loads(content.strip())
            if isinstance(parsed, dict) and 'controls' in parsed:
                return parsed['controls']
            elif isinstance(parsed, list):
                return parsed
            return []
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            return []

    def _check_lm_studio(self) -> bool:
        """Check if LM Studio is available"""
        try:
            response = requests.get(f"{self.lm_studio_host}/v1/models", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LM Studio not available at {self.lm_studio_host}: {e}")
            return False
    
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available at {self.ollama_host}: {e}")
            return False
    
    def _extract_with_ollama(self, text: str) -> List[Dict]:
        """Extract controls using Ollama"""

        try:
            prompt = self.extraction_prompt.format(text=text)

            logger.info(f"Ollama model: {self.ollama_model}")
            logger.info(f"Ollama prompt length: {len(prompt)}")

            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0,
                        "top_p": 0.1,
                        "num_predict": 250
                    }
                },
                timeout=300
            )

            logger.error(f"Ollama RAW HTTP response: {response.text}")

            response.raise_for_status()

            response_json = response.json()

            content = response_json.get("response", "")

            logger.error(f"Ollama extracted content: {content}")

            if not content or not content.strip():
                logger.error("Ollama returned empty content")
                return []

            # Remove markdown wrappers if present
            content = re.sub(r"```json|```", "", content).strip()

            try:
                parsed = json.loads(content)

                logger.info(f"Parsed response type: {type(parsed)}")

                # Case 1: {"controls": [...]}
                if isinstance(parsed, dict):
                    if "controls" in parsed:
                        controls = parsed["controls"]

                        logger.info(
                            f"Extracted {len(controls)} controls from Ollama"
                        )

                        return controls

                    logger.warning(
                        "Parsed JSON object but no 'controls' key found"
                    )

                    logger.warning(f"Available keys: {list(parsed.keys())}")

                # Case 2: direct array [...]
                elif isinstance(parsed, list):

                    logger.info(
                        f"Extracted {len(parsed)} controls from direct array"
                    )

                    return parsed

                else:
                    logger.warning(
                        f"Unexpected parsed type: {type(parsed)}"
                    )

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse failed: {e}")
                logger.error(f"Content was: {content}")

            return []

        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return []

        except requests.exceptions.ConnectionError:
            logger.error(
                f"Could not connect to Ollama at {self.ollama_host}"
            )
            return []

        except Exception as e:
            logger.error(f"Ollama extraction failed: {str(e)}")
            return []


    def _extract_with_lm_studio(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """Extract controls using LM Studio"""

        import json
        import time

        try:

            logger.info(
                f"Using LM Studio ({self.lm_studio_model})"
            )

            prompt = self.extraction_prompt.format(
                text=text
            )

            payload = {
                "model": self.lm_studio_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You extract compliance controls "
                            "and return ONLY valid JSON."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0,
                "top_p": 0.1,
                "max_tokens": 800,
                "stream": False
            }

            logger.info("=" * 80)
            logger.info("LM STUDIO REQUEST")
            logger.info("=" * 80)
            logger.info(
                f"Prompt length: {len(prompt)}"
            )

            start_time = time.time()

            response = requests.post(
                f"{self.lm_studio_host}/v1/chat/completions",
                json=payload,
                timeout=600,
                headers={
                    "Content-Type": "application/json"
                }
            )

            elapsed = round(
                time.time() - start_time,
                2
            )

            logger.info(
                f"LM Studio completed in {elapsed}s"
            )

            logger.info(
                f"HTTP Status: {response.status_code}"
            )

            response.raise_for_status()

            result = response.json()

            logger.info("RAW RESPONSE:")
            logger.info(
                json.dumps(result, indent=2)[:5000]
            )

            finish_reason = (
                result
                .get("choices", [{}])[0]
                .get("finish_reason")
            )

            logger.info(
                f"Finish reason: {finish_reason}"
            )

            if finish_reason == "length":
                logger.warning(
                    "Response truncated due to max_tokens"
                )

            content = (
                result
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            if not content:

                logger.error(
                    "LM Studio returned empty content"
                )

                return []

            logger.info("MODEL CONTENT:")
            logger.info(content[:5000])

            # Remove markdown wrappers
            cleaned = re.sub(
                r'```(?:json)?|```',
                '',
                content
            ).strip()

            # Extract JSON object safely
            start = cleaned.find('{')
            end = cleaned.rfind('}')

            if start != -1 and end != -1:
                cleaned = cleaned[start:end + 1]

            logger.info("CLEANED JSON:")
            logger.info(cleaned[:5000])

            try:

                parsed = json.loads(cleaned)

                # Case 1
                if (
                    isinstance(parsed, dict)
                    and "controls" in parsed
                ):

                    controls = parsed["controls"]

                    logger.info(
                        f"Extracted {len(controls)} controls"
                    )

                    return controls

                # Case 2
                if isinstance(parsed, list):

                    logger.info(
                        f"Extracted {len(parsed)} controls"
                    )

                    return parsed

                logger.error(
                    "Unexpected JSON structure"
                )

                return []

            except json.JSONDecodeError as e:

                logger.error(
                    f"JSON parse failed: {e}"
                )

                logger.error(
                    f"Failed JSON:\n{cleaned[:5000]}"
                )

                return []

        except requests.exceptions.Timeout:

            logger.error(
                "LM Studio request timed out"
            )

            return []

        except requests.exceptions.ConnectionError as e:

            logger.error(
                f"LM Studio connection failed: {e}"
            )

            return []

        except Exception as e:

            logger.exception(
                f"LM Studio extraction failed: {e}"
            )

            return []


    def extract_from_pdf_bytes(self, content: bytes) -> List[Dict[str, Any]]:
        """
        Extract controls from PDF bytes
        
        Args:
            content: PDF file content as bytes
            
        Returns:
            List of extracted controls
        """
        # Check for mock mode first (useful for development/demos)
        from config import get_config
        config = get_config()
        if config.mock_mode:
            logger.info("Mock mode enabled: returning sample controls")
            return self._get_mock_controls()
            
        try:
            # Try PyPDF2 first
            text = self._extract_text_pypdf2(content)
            
            # If PyPDF2 fails or returns little text, try pdfplumber
            if not text or len(text) < 100:
                text = self._extract_text_pdfplumber(content)
            
            if not text:
                logger.error("Failed to extract text from PDF")
                return []
            
            # Extract controls using AI
            try:
                return self._extract_controls_with_ai(text)
            except Exception as e:
                logger.warning(f"AI extraction failed, attempting fallback regex extraction: {e}")
                fallback_controls = self._extract_controls_fallback(text)
                if fallback_controls:
                    logger.info(f"Successfully extracted {len(fallback_controls)} controls via fallback")
                    return fallback_controls
                raise
            
        except Exception as e:
            logger.error(f"Error extracting from PDF: {e}")
            # If everything fails, return empty list but ensure it was logged
            return []
    
    def extract_from_url(self, url: str) -> List[Dict[str, Any]]:
        """
        Extract controls from PDF URL
        
        Args:
            url: URL to PDF document
            
        Returns:
            List of extracted controls
        """
        try:
            logger.info(f"Downloading PDF from {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            return self.extract_from_pdf_bytes(response.content)
            
        except Exception as e:
            logger.error(f"Error downloading PDF from URL: {e}")
            return []
    
    def _extract_text_pypdf2(self, content: bytes) -> str:
        """Extract text using PyPDF2"""
        try:
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
            return ""
    
    def _extract_text_pdfplumber(self, content: bytes) -> str:
        """Extract text using pdfplumber (better for complex PDFs)"""
        try:
            pdf_file = io.BytesIO(content)
            text_parts = []
            
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return ""
    
    def _extract_controls_with_ai(self, text: str, chunk_size: int = 8000) -> List[Dict[str, Any]]:
        """
        Extract controls from text using AI
        
        Args:
            text: Extracted text from PDF
            chunk_size: Maximum characters per chunk
            
        Returns:
            List of extracted controls
        """
        import json
        
        try:
            # Split text into chunks if too long
            chunks = self._split_text(text, chunk_size)
            all_controls = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                prompt = self.extraction_prompt.format(text=chunk)
                chunk_controls = None
                
                # Use only the configured extraction method
                if self.anthropic_enabled:
                    if not self.anthropic_client:
                        raise ValueError("Anthropic/OpenCode Zen is enabled but API key is not configured")
                    logger.info(f"Using Anthropic/OpenCode Zen for chunk {i+1}")
                    chunk_controls = self._extract_with_anthropic(chunk)

                elif self.opencode_enabled:
                    if not self.opencode_client:
                        raise ValueError("OpenCode Zen is enabled but API key is not configured")
                    logger.info(f"Using OpenCode Zen for chunk {i+1}")
                    chunk_controls = self._extract_with_opencode(chunk)

                elif self.lm_studio_enabled:
                    if not self.lm_studio_available:
                        raise ValueError(f"LM Studio is enabled but not available at {self.lm_studio_host}")
                    logger.info(f"Using LM Studio for chunk {i+1}")
                    chunk_controls = self._extract_with_lm_studio(chunk)

                elif self.openai_enabled:
                    if not self.client:
                        raise ValueError("OpenAI is enabled but API key is not configured")
                    logger.info(f"Using OpenAI for chunk {i+1}")
                    chunk_controls = self._extract_with_openai(chunk)

                elif self.ollama_enabled:
                    if not self.ollama_available:
                        raise ValueError(f"Ollama is enabled but not available at {self.ollama_host}")
                    logger.info(f"Using Ollama for chunk {i+1}")
                    chunk_controls = self._extract_with_ollama(chunk)
                
                # Add controls to results
                if chunk_controls and isinstance(chunk_controls, list):
                    all_controls.extend(chunk_controls)
                else:
                    logger.error(f"No controls extracted from chunk {i+1}")
            
            # Validate we got controls
            if not all_controls:
                raise ValueError("No controls extracted from any chunks. Check your extraction service configuration and PDF content.")
            
            # Deduplicate controls by control_id
            unique_controls = {}
            for control in all_controls:
                control_id = control.get('control_id')
                if control_id and control_id not in unique_controls:
                    unique_controls[control_id] = control
            
            result = list(unique_controls.values())
            logger.info(f"Successfully extracted {len(result)} unique controls from PDF")
            return result
            
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            # Do not use mock fallback - raise the error
            raise RuntimeError(f"Failed to extract controls from PDF: {e}") from e
    
    
    def _extract_controls_fallback(self, text: str) -> List[Dict[str, Any]]:
        """
        Fallback extraction using regex patterns when AI fails.
        Useful for structured compliance documents.
        """
        controls = []
        
        # Pattern for SOC2/ISO-style controls: ID followed by description and severity
        # Example: SOC2-CC1.1 - description - high - category
        pattern = r'(SOC2-[A-Z0-9\.]+|ISO-[0-9\.]+|CTRL-[0-9]+)[\s\:\-]+(.*?)(?=\n(?:SOC2|ISO|CTRL|$))'
        matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(matches):
            cid = match.group(1).strip()
            content = match.group(2).strip()
            
            # Try to split content into description/severity/category if possible
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            description = lines[0] if lines else "No description available"
            
            severity = "medium"
            category = "General"
            
            for line in lines[1:]:
                l_lower = line.lower()
                if any(s in l_lower for s in ['critical', 'high', 'medium', 'low']):
                    severity = l_lower
                elif len(line) > 3:
                    category = line
            
            controls.append({
                "control_id": cid,
                "description": description,
                "condition": "exists(event.status)",  # Default condition
                "severity": severity,
                "remediation": f"Verify compliance for {cid}",
                "category": category,
                "standard": "SOC2" if "SOC2" in cid.upper() else "Compliance",
                "control_type": "detective",
                "evidence_required": "Log evidence",
                "automatable": True
            })
        
        # If no regex matches, try a simpler line-based split for very basic documents
        if not controls and len(text.strip()) > 50:
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 20]
            for i, line in enumerate(lines[:10]):
                controls.append({
                    "control_id": f"EXTRACTED-{i+1:03d}",
                    "description": line,
                    "condition": "exists(event.status)",
                    "severity": "medium",
                    "remediation": "Review compliance requirement",
                    "category": "General",
                    "standard": "Custom",
                    "control_type": "detective",
                    "evidence_required": "Manual review",
                    "automatable": False
                })
                
        return controls


    def _get_mock_controls(self) -> List[Dict[str, Any]]:
        """Return sample controls for demo/mock mode"""
        return [
            {
                "control_id": "SOC2-CC6.1",
                "description": "Ensure logical access to systems is restricted to authorized users.",
                "condition": "event.event_name == 'login' and event.status == 'success'",
                "severity": "critical",
                "remediation": "Review access logs and revoke unauthorized permissions.",
                "category": "Logical Access",
                "standard": "SOC2",
                "control_type": "preventive",
                "evidence_required": "Access control lists and IAM policies",
                "automatable": True
            },
            {
                "control_id": "SOC2-CC7.2",
                "description": "Identify and evaluate vulnerabilities in the system periodically.",
                "condition": "event.resource_type == 'vulnerability_scan' and event.vulnerabilities_found > 0",
                "severity": "high",
                "remediation": "Apply security patches and updates to affected systems.",
                "category": "System Operations",
                "standard": "SOC2",
                "control_type": "detective",
                "evidence_required": "Vulnerability scan reports",
                "automatable": True
            }
        ]

    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        # Split by paragraphs
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks


# Legacy function for backward compatibility
def extract_controls_from_pdf(content: bytes, openai_api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract controls from PDF content
    
    Args:
        content: PDF file content as bytes
        openai_api_key: OpenAI API key (optional, will use env var if not provided)
        
    Returns:
        List of extracted controls
    """
    import os
    api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        logger.error("OpenAI API key not provided")
        return []
    
    extractor = ComplianceExtractor(api_key)
    return extractor.extract_from_pdf_bytes(content)

# Made with Bob
