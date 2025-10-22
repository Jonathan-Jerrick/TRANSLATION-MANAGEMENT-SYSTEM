"""LLM integration service for translation and quality estimation."""
from __future__ import annotations

import asyncio
import os
from typing import Dict, List, Optional

import anthropic
import google.generativeai as genai
from openai import AsyncOpenAI

from .models import RiskLevel


class LLMService:
    """Service for LLM-powered translation and quality estimation."""

    def __init__(self) -> None:
        self.openai_client = self._init_openai_client()
        self.anthropic_client = self._init_anthropic_client()
        self.google_model = self._init_google_model()

    def _init_openai_client(self) -> Optional[AsyncOpenAI]:
        """Return an OpenAI client when credentials are available."""

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            return AsyncOpenAI(api_key=api_key)
        except Exception:
            return None

    def _init_anthropic_client(self) -> Optional[anthropic.AsyncAnthropic]:
        """Return an Anthropic client when credentials are available."""

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        try:
            return anthropic.AsyncAnthropic(api_key=api_key)
        except Exception:
            return None

    def _init_google_model(self):
        """Return a Google GenerativeModel when credentials are available."""

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None
        try:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel("gemini-pro")
        except Exception:
            return None

    async def _fallback_translation(self, text: str) -> Dict[str, object]:
        """Deterministic fallback when no external provider is available."""

        return {
            "translation": text if text else "",
            "confidence": 0.6,
            "provider": "stub",
        }

    def _fallback_quality(self, source_text: str, translated_text: str) -> Dict[str, object]:
        """Provide a simple heuristic quality response."""

        if not translated_text:
            return {
                "quality_score": 55.0,
                "risk_level": RiskLevel.HIGH.value,
                "issues": ["Translation output was empty"],
                "suggestions": ["Re-run MT or assign human translator."],
            }

        similarity = min(len(translated_text), len(source_text)) / max(len(translated_text), len(source_text), 1)
        quality = round(70 + similarity * 25, 2)
        if quality >= 85:
            risk = RiskLevel.LOW.value
        elif quality >= 70:
            risk = RiskLevel.MEDIUM.value
        else:
            risk = RiskLevel.HIGH.value

        return {
            "quality_score": min(100.0, quality),
            "risk_level": risk,
            "issues": [],
            "suggestions": ["Proceed with reviewer spot-checks."],
        }

    def _fallback_suggestions(self, source_text: str, translated_text: str) -> List[str]:
        """Generate lightweight improvement suggestions without APIs."""

        suggestions: List[str] = []
        if source_text and translated_text and source_text.lower() == translated_text.lower():
            suggestions.append("Localise terminology instead of mirroring the source text.")
        if len(translated_text.split()) < len(source_text.split()):
            suggestions.append("Ensure important qualifiers from the source are preserved.")
        suggestions.append("Have a reviewer validate tone and style for the target market.")
        return suggestions

    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[str] = None,
        provider: str = "openai",
    ) -> Dict[str, object]:
        """Translate text using the specified LLM provider."""

        prompt = self._create_translation_prompt(text, source_lang, target_lang, context)

        try:
            if provider == "openai":
                if self.openai_client:
                    return await self._translate_with_openai(prompt)
                return await self._fallback_translation(text)
            if provider == "anthropic":
                if self.anthropic_client:
                    return await self._translate_with_anthropic(prompt)
                return await self._fallback_translation(text)
            if provider == "google":
                if self.google_model:
                    return await self._translate_with_google(prompt)
                return await self._fallback_translation(text)
            raise ValueError(f"Unsupported provider: {provider}")
        except Exception:
            return await self._fallback_translation(text)

    async def estimate_quality(
        self,
        source_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
    ) -> Dict[str, object]:
        """Estimate translation quality using an LLM or heuristics."""

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
            if not self.openai_client:
                raise RuntimeError("openai client unavailable")
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            import json

            return json.loads(response.choices[0].message.content)
        except Exception:
            return self._fallback_quality(source_text, translated_text)

    async def suggest_improvements(
        self,
        source_text: str,
        translated_text: str,
        context: Optional[str] = None,
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
            if not self.openai_client:
                raise RuntimeError("openai client unavailable")
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            suggestions = response.choices[0].message.content.split("\n")
            return [item.strip() for item in suggestions if item.strip()]
        except Exception:
            return self._fallback_suggestions(source_text, translated_text)

    async def extract_terminology(
        self,
        text: str,
        domain: str = "general",
    ) -> List[Dict[str, str]]:
        """Extract terminology using LLMs or heuristics."""

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
            if not self.openai_client:
                raise RuntimeError("openai client unavailable")
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            import json

            return json.loads(response.choices[0].message.content)
        except Exception:
            terms: List[Dict[str, str]] = []
            for candidate in text.split():
                cleaned = candidate.strip(".,;:!?")
                if cleaned.isupper() or (cleaned.istitle() and len(cleaned) > 6):
                    terms.append(
                        {
                            "term": cleaned,
                            "definition": "Key domain term identified heuristically.",
                            "importance": "medium",
                        }
                    )
            return terms

    def _create_translation_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[str] = None,
    ) -> str:
        """Create a translation prompt."""

        base_prompt = f"Translate the following text from {source_lang} to {target_lang}:"
        if context:
            base_prompt += f"\n\nContext: {context}"
        base_prompt += f"\n\nText: {text}"
        base_prompt += "\n\nProvide only the translation, maintaining the original tone and style."
        return base_prompt

    async def _translate_with_openai(self, prompt: str) -> Dict[str, object]:
        """Translate using OpenAI."""

        if not self.openai_client:
            return await self._fallback_translation("")

        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        return {
            "translation": response.choices[0].message.content.strip(),
            "confidence": 0.85,
            "provider": "openai",
        }

    async def _translate_with_anthropic(self, prompt: str) -> Dict[str, object]:
        """Translate using Anthropic."""

        if not self.anthropic_client:
            return await self._fallback_translation("")

        response = await self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "translation": response.content[0].text.strip(),
            "confidence": 0.8,
            "provider": "anthropic",
        }

    async def _translate_with_google(self, prompt: str) -> Dict[str, object]:
        """Translate using Google Gemini."""

        if not self.google_model:
            return await self._fallback_translation("")

        response = await self.google_model.generate_content_async(prompt)

        return {
            "translation": response.text.strip(),
            "confidence": 0.75,
            "provider": "google",
        }

    async def batch_translate(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        provider: str = "openai",
    ) -> List[Dict[str, object]]:
        """Translate multiple texts in batch."""

        tasks = [
            self.translate_text(text, source_lang, target_lang, provider=provider)
            for text in texts
        ]
        return await asyncio.gather(*tasks)

    async def get_translation_confidence(
        self,
        source_text: str,
        translated_text: str,
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
            if not self.openai_client:
                raise RuntimeError("openai client unavailable")
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            import re

            numbers = re.findall(r"\d+", response.choices[0].message.content)
            if numbers:
                return min(100, max(0, int(numbers[0])))
            return 50.0
        except Exception:
            baseline = 65.0
            if translated_text and translated_text.strip() == source_text.strip():
                baseline = 72.0
            if len(translated_text.split()) < max(len(source_text.split()), 1) / 2:
                baseline = 58.0
            return baseline
