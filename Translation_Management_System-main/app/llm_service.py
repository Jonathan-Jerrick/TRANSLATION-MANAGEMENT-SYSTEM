"""LLM integration service for translation and quality estimation."""
import os
import asyncio
from typing import Dict, List, Optional, Tuple
from openai import AsyncOpenAI
import anthropic
import google.generativeai as genai
import httpx
from .models import RiskLevel

# Initialize clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class LLMService:
    """Service for LLM-powered translation and quality estimation."""
    
    def __init__(self):
        self.openai_client = openai_client
        self.anthropic_client = anthropic_client
        self.google_model = genai.GenerativeModel('gemini-pro')
    
    async def translate_text(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str,
        context: Optional[str] = None,
        provider: str = "openai"
    ) -> Dict[str, any]:
        """Translate text using specified LLM provider."""
        
        # Create translation prompt
        prompt = self._create_translation_prompt(text, source_lang, target_lang, context)
        
        try:
            if provider == "openai":
                return await self._translate_with_openai(prompt)
            elif provider == "anthropic":
                return await self._translate_with_anthropic(prompt)
            elif provider == "google":
                return await self._translate_with_google(prompt)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except Exception as e:
            return {
                "translation": text,  # Fallback to original text
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def estimate_quality(
        self, 
        source_text: str, 
        translated_text: str,
        source_lang: str,
        target_lang: str
    ) -> Dict[str, any]:
        """Estimate translation quality using LLM."""
        
        prompt = f"""
        Analyze the quality of this translation:
        
        Source ({source_lang}): {source_text}
        Translation ({target_lang}): {translated_text}
        
        Provide:
        1. Quality score (0-100)
        2. Risk level (low/medium/high)
        3. Specific issues found
        4. Suggestions for improvement
        
        Respond in JSON format:
        {{
            "quality_score": <number>,
            "risk_level": "<low|medium|high>",
            "issues": ["issue1", "issue2"],
            "suggestions": ["suggestion1", "suggestion2"]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Parse JSON response
            import json
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {
                "quality_score": 50,
                "risk_level": "medium",
                "issues": ["Quality estimation failed"],
                "suggestions": ["Manual review recommended"]
            }
    
    async def suggest_improvements(
        self, 
        source_text: str, 
        translated_text: str,
        context: Optional[str] = None
    ) -> List[str]:
        """Suggest improvements for a translation."""
        
        prompt = f"""
        Suggest improvements for this translation:
        
        Source: {source_text}
        Translation: {translated_text}
        Context: {context or "No additional context"}
        
        Provide 3-5 specific suggestions for improvement.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            # Parse suggestions
            suggestions = response.choices[0].message.content.split('\n')
            return [s.strip() for s in suggestions if s.strip()]
        except Exception as e:
            return ["Manual review recommended"]
    
    async def extract_terminology(
        self, 
        text: str, 
        domain: str = "general"
    ) -> List[Dict[str, str]]:
        """Extract domain-specific terminology from text."""
        
        prompt = f"""
        Extract key terminology from this {domain} text:
        
        {text}
        
        For each term, provide:
        1. The term itself
        2. Its definition/explanation
        3. Its importance level (high/medium/low)
        
        Respond in JSON format:
        [
            {{
                "term": "term1",
                "definition": "definition1",
                "importance": "high"
            }}
        ]
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            import json
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return []
    
    def _create_translation_prompt(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str,
        context: Optional[str] = None
    ) -> str:
        """Create a translation prompt."""
        base_prompt = f"Translate the following text from {source_lang} to {target_lang}:"
        if context:
            base_prompt += f"\n\nContext: {context}"
        base_prompt += f"\n\nText: {text}"
        base_prompt += "\n\nProvide only the translation, maintaining the original tone and style."
        return base_prompt
    
    async def _translate_with_openai(self, prompt: str) -> Dict[str, any]:
        """Translate using OpenAI."""
        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return {
            "translation": response.choices[0].message.content.strip(),
            "confidence": 0.85,  # GPT-4 confidence estimate
            "provider": "openai"
        }
    
    async def _translate_with_anthropic(self, prompt: str) -> Dict[str, any]:
        """Translate using Anthropic."""
        response = await self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "translation": response.content[0].text.strip(),
            "confidence": 0.80,  # Claude confidence estimate
            "provider": "anthropic"
        }
    
    async def _translate_with_google(self, prompt: str) -> Dict[str, any]:
        """Translate using Google Gemini."""
        response = await self.google_model.generate_content_async(prompt)
        
        return {
            "translation": response.text.strip(),
            "confidence": 0.75,  # Gemini confidence estimate
            "provider": "google"
        }
    
    async def batch_translate(
        self, 
        texts: List[str], 
        source_lang: str, 
        target_lang: str,
        provider: str = "openai"
    ) -> List[Dict[str, any]]:
        """Translate multiple texts in batch."""
        tasks = [
            self.translate_text(text, source_lang, target_lang, provider=provider)
            for text in texts
        ]
        return await asyncio.gather(*tasks)
    
    async def get_translation_confidence(
        self, 
        source_text: str, 
        translated_text: str
    ) -> float:
        """Get confidence score for a translation."""
        prompt = f"""
        Rate the confidence of this translation (0-100):
        
        Source: {source_text}
        Translation: {translated_text}
        
        Consider accuracy, fluency, and cultural appropriateness.
        Respond with only a number between 0 and 100.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Extract number from response
            import re
            numbers = re.findall(r'\d+', response.choices[0].message.content)
            if numbers:
                return min(100, max(0, int(numbers[0])))
            return 50.0
        except Exception:
            return 50.0
