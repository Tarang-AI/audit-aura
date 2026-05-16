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
from concurrent.futures import ThreadPoolExecutor

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
You are a world-class Cybersecurity Compliance Auditor and Data Scientist.
Your task is to extract compliance controls from audit documents with surgical precision.

### EXTRACTION RULES:
1. **IDENTIFY AUDIT STANDARD**: Locate the specific standard (e.g., SOC 2 Type II, BSI C5:2020, ISO/IEC 27001:2022). Do NOT use 'Custom' or 'Unknown'.
2. **CONTROL IDs**: Extract the EXACT alphanumeric ID (e.g., CC6.1, OPS-01, A.5.1). Do NOT generate arbitrary numbers.
3. **CATEGORIES**: Group controls into professional compliance domains:
   - Access Control & Identity
   - Network & Infrastructure Security
   - Data Protection & Encryption
   - Operational Security & Change Management
   - Governance, Risk & Compliance (GRC)
   - Physical & Environmental Security
   - Incident Response & Business Continuity
4. **DESCRIPTIONS**: Provide a detailed, professional summary of the requirement. DO NOT truncate.
5. **TITLES**: Create a clear, high-level name for the control.

### OUTPUT FORMAT:
Return ONLY valid JSON. No prose. No markdown.

{{
  "controls": [
    {{
      "control_id": "C5-OPS-01",
      "title": "Change Management Process",
      "description": "The provider implements a formal change management process to ensure that all changes to information systems, including software and hardware, are documented, tested, and approved prior to implementation.",
      "condition": "exists(event.change_id) and event.status == 'approved'",
      "severity": "high",
      "remediation": "Review unapproved changes and enforce the formal change management workflow.",
      "category": "Operational Security & Change Management",
      "standard": "C5",
      "control_type": "preventive",
      "evidence_required": "Change request logs and approval records",
      "automatable": true
    }}
  ]
}}


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
                max_tokens=4000,
                temperature=0,
                system="You are a compliance expert that extracts controls from audit documents. Always respond with valid JSON objects containing a 'controls' array.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Handle multiple content blocks (some might be ThinkingBlocks or TextBlocks)
            content = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    content = block.text
                    break
            
            if not content:
                logger.warning("No text content found in Anthropic response")
                return []
            
            # Clean markdown and common LLM prose
            cleaned = content.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            
            # Find the first { and last } to isolate JSON
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end + 1]
            
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and 'controls' in parsed:
                    return parsed['controls']
                elif isinstance(parsed, list):
                    return parsed
                return []
            except json.JSONDecodeError as je:
                logger.error(f"JSON Decode Error at char {je.pos}: {je.msg}")
                # Try a very aggressive recovery: find all {} objects that look like controls
                recovered = self._recover_json_controls(cleaned)
                if recovered:
                    logger.info(f"Recovered {len(recovered)} controls from malformed JSON")
                return recovered
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
            
            logger.info(f"Extracted {len(text)} characters from PDF")
            
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
    
    def _process_chunk(self, i: int, chunk: str, total: int) -> List[Dict[str, Any]]:
        """Helper to process a single chunk in a thread"""
        try:
            logger.info(f"Processing chunk {i+1}/{total}")
            
            # Use only the configured extraction method
            if self.anthropic_enabled:
                if not self.anthropic_client:
                    return []
                return self._extract_with_anthropic(chunk)

            elif self.opencode_enabled:
                if not self.opencode_client:
                    return []
                return self._extract_with_opencode(chunk)

            elif self.lm_studio_enabled:
                if not self.lm_studio_available:
                    return []
                return self._extract_with_lm_studio(chunk)

            elif self.openai_enabled:
                if not self.client:
                    return []
                return self._extract_with_openai(chunk)

            elif self.ollama_enabled:
                if not self.ollama_available:
                    return []
                return self._extract_with_ollama(chunk)
            
            return []
        except Exception as e:
            logger.error(f"Error processing chunk {i+1}: {e}")
            return []

    def _extract_controls_with_ai(self, text: str, chunk_size: int = 2000) -> List[Dict[str, Any]]:
        """
        Extract controls from text using AI (Parallel Processing)
        """
        try:
            # Split text into chunks
            chunks = self._split_text(text, chunk_size)
            all_controls = []
            total_chunks = len(chunks)
            
            logger.info(f"Starting parallel extraction for {total_chunks} chunks using 5 workers")
            
            # Process chunks in parallel
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Submit all chunks to the executor
                futures = [executor.submit(self._process_chunk, i, chunk, total_chunks) for i, chunk in enumerate(chunks)]
                
                # Gather results as they complete
                for future in futures:
                    try:
                        chunk_controls = future.result()
                        if chunk_controls and isinstance(chunk_controls, list):
                            all_controls.extend(chunk_controls)
                    except Exception as e:
                        logger.error(f"Failed to retrieve results for chunk: {e}")
            
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
        Improved fallback extraction using regex patterns for common control formats
        """
        controls = []
        
        # Patterns for IDs like CC6.1, OPS-01, A.5.1
        id_patterns = [
            r'([A-Z]{1,4}\s?\d{1,3}(?:\.\d{1,3})*)',  # CC6.1, A.5.1
            r'([A-Z]{2,5}-\d{2,3})',                 # OPS-01
            r'(?:Control|Requirement)\s?#?\s?(\d{1,3}(?:\.\d{1,3})*)' # Control 1.1
        ]
        
        # Detect standard
        standard = "Custom"
        if re.search(r'SOC\s?2', text, re.I): standard = "SOC2"
        elif re.search(r'C5', text, re.I): standard = "C5"
        elif re.search(r'ISO\s?27001', text, re.I): standard = "ISO27001"
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) < 30: continue
            
            found_id = None
            for pattern in id_patterns:
                match = re.search(pattern, line)
                if match:
                    found_id = match.group(1)
                    break
            
            if found_id or (len(line) > 50 and i % 10 == 0): # Extract every 10th long line as a fallback
                control_id = found_id if found_id else f"{standard}-{i}"
                controls.append({
                    "control_id": control_id,
                    "title": line[:50] + "..." if len(line) > 50 else line,
                    "description": line,
                    "condition": "exists(event.status)",
                    "severity": "medium",
                    "remediation": f"Verify compliance for {control_id}",
                    "category": "Governance, Risk & Compliance (GRC)",
                    "standard": standard,
                    "control_type": "detective",
                    "evidence_required": "Log evidence",
                    "automatable": True
                })
            
            if len(controls) >= 50: break
            
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
        """Split text into chunks of maximum chunk_size"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        # Split by double newlines first (paragraphs)
        parts = re.split(r'\n\n+', text)
        
        current_chunk = ""
        for part in parts:
            if len(part) > chunk_size:
                # Part itself is too big, split by single newline
                sub_parts = part.split('\n')
                for sub_part in sub_parts:
                    if len(sub_part) > chunk_size:
                        # Even single line is too big, split by characters
                        for i in range(0, len(sub_part), chunk_size):
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = ""
                            chunks.append(sub_part[i:i+chunk_size].strip())
                    elif len(current_chunk) + len(sub_part) + 1 > chunk_size:
                        chunks.append(current_chunk.strip())
                        current_chunk = sub_part
                    else:
                        current_chunk = f"{current_chunk}\n{sub_part}" if current_chunk else sub_part
            elif len(current_chunk) + len(part) + 2 > chunk_size:
                chunks.append(current_chunk.strip())
                current_chunk = part
            else:
                current_chunk = f"{current_chunk}\n\n{part}" if current_chunk else part
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks


    def _recover_json_controls(self, text: str) -> List[Dict[str, Any]]:
        """Attempt to recover control objects from malformed JSON string"""
        controls = []
        try:
            import json
            # Look for patterns like {"control_id": "...", ...}
            # This is a last resort
            potential_objects = re.findall(r'\{[^{}]*?"control_id"[^{}]*?\}', text, re.DOTALL)
            for obj_str in potential_objects:
                try:
                    # Try to fix common issues like missing quotes or trailing commas
                    fixed = re.sub(r',\s*\}', '}', obj_str)
                    obj = json.loads(fixed)
                    if 'control_id' in obj:
                        controls.append(obj)
                except:
                    continue
        except:
            pass
        return controls

    def _extract_controls_fallback(self, text: str) -> List[Dict[str, Any]]:
        """
        Improved fallback extraction using regex patterns for common control formats
        """
        controls = []
        
        # Patterns for IDs like CC6.1, OPS-01, A.5.1
        id_patterns = [
            r'([A-Z]{1,4}\s?\d{1,3}(?:\.\d{1,3})*)',  # CC6.1, A.5.1
            r'([A-Z]{2,5}-\d{2,3})',                 # OPS-01
            r'(?:Control|Requirement)\s?#?\s?(\d{1,3}(?:\.\d{1,3})*)' # Control 1.1
        ]
        
        # Detect standard
        standard = "Custom"
        if re.search(r'SOC\s?2', text, re.I): standard = "SOC2"
        elif re.search(r'C5', text, re.I): standard = "C5"
        elif re.search(r'ISO\s?27001', text, re.I): standard = "ISO27001"
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) < 30: continue
            
            found_id = None
            for pattern in id_patterns:
                match = re.search(pattern, line)
                if match:
                    found_id = match.group(1)
                    break
            
            if found_id or (len(line) > 50 and i % 10 == 0): # Extract every 10th long line as a fallback
                control_id = found_id if found_id else f"{standard}-{i}"
                controls.append({
                    "control_id": control_id,
                    "title": line[:50] + "..." if len(line) > 50 else line,
                    "description": line,
                    "condition": "exists(event.status)",
                    "severity": "medium",
                    "remediation": f"Verify compliance for {control_id}",
                    "category": "General Security",
                    "standard": standard,
                    "control_type": "detective",
                    "evidence_required": "Log evidence",
                    "automatable": True
                })
            
            if len(controls) >= 50: break
            
        return controls

# Legacy function for backward compatibility
def extract_controls_from_pdf(content: bytes, openai_api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract controls from PDF content
    """
    import os
    api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        return []
    extractor = ComplianceExtractor(openai_api_key=api_key, openai_enabled=True)
    return extractor.extract_from_pdf_bytes(content)

