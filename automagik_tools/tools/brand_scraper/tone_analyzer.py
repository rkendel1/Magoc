"""
Tone and Voice Analyzer - Analyze text content for brand voice and tone
"""

import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import httpx


class ToneAnalyzer:
    """Analyze website text for voice and tone characteristics"""

    def __init__(
        self, timeout: int = 30, user_agent: str = "", max_text_length: int = 10000
    ):
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; BrandScraperBot/1.0)"
        self.max_text_length = max_text_length

        # Define keyword patterns for tone detection
        self.tone_keywords = {
            "formal": [
                "therefore",
                "furthermore",
                "moreover",
                "consequently",
                "nevertheless",
            ],
            "casual": ["hey", "cool", "awesome", "yeah", "super", "totally"],
            "professional": [
                "expertise",
                "experience",
                "solutions",
                "services",
                "commitment",
            ],
            "friendly": ["welcome", "happy", "excited", "love", "enjoy"],
            "technical": [
                "optimize",
                "algorithm",
                "infrastructure",
                "implementation",
                "architecture",
            ],
            "empathetic": ["understand", "care", "support", "help", "together"],
            "urgent": ["now", "today", "immediately", "urgent", "hurry"],
            "confident": ["guarantee", "ensure", "proven", "trusted", "reliable"],
        }

    async def extract(
        self, url: str, html_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze tone and voice from a URL or HTML content

        Args:
            url: The URL to analyze
            html_content: Optional pre-fetched HTML content

        Returns:
            Dictionary with tone and voice analysis
        """
        if not html_content:
            html_content = await self._fetch_page(url)

        soup = BeautifulSoup(html_content, "html.parser")

        # Extract text content
        text_content = self._extract_text(soup)

        # Analyze tone
        tone_scores = self._analyze_tone(text_content)
        sentiment = self._simple_sentiment(text_content)
        characteristics = self._analyze_characteristics(text_content)

        return {
            "tone": tone_scores,
            "sentiment": sentiment,
            "characteristics": characteristics,
            "text_samples": self._extract_key_phrases(text_content),
            "metadata": {
                "url": url,
                "word_count": len(text_content.split()),
                "char_count": len(text_content),
            },
        }

    async def _fetch_page(self, url: str) -> str:
        """Fetch page content via HTTP"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {"User-Agent": self.user_agent}
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.text

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text from specific content areas
        text_sources = []

        # Try to find main content areas
        main_content = (
            soup.find("main") or soup.find("article") or soup.find(class_="content")
        )
        if main_content:
            text_sources.append(main_content.get_text())

        # Get heading texts
        for heading in soup.find_all(["h1", "h2", "h3"]):
            text_sources.append(heading.get_text())

        # Get paragraph texts
        for para in soup.find_all("p"):
            text_sources.append(para.get_text())

        # Combine and clean
        text = " ".join(text_sources)
        text = re.sub(r"\s+", " ", text).strip()

        # Limit length
        return text[: self.max_text_length]

    def _analyze_tone(self, text: str) -> Dict[str, float]:
        """Analyze tone using keyword patterns"""
        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)

        if word_count == 0:
            return {}

        tone_scores = {}

        for tone, keywords in self.tone_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            # Normalize score (0-1 range)
            score = min(matches / (word_count / 100), 1.0)  # Per 100 words
            tone_scores[tone] = round(score, 3)

        # Identify dominant tones
        sorted_tones = sorted(tone_scores.items(), key=lambda x: x[1], reverse=True)

        return {
            "scores": tone_scores,
            "dominant": sorted_tones[0][0] if sorted_tones else "neutral",
            "secondary": sorted_tones[1][0] if len(sorted_tones) > 1 else None,
        }

    def _simple_sentiment(self, text: str) -> Dict[str, Any]:
        """Simple sentiment analysis using keyword matching"""
        text_lower = text.lower()

        # Positive and negative word lists
        positive_words = [
            "good",
            "great",
            "excellent",
            "amazing",
            "wonderful",
            "fantastic",
            "love",
            "best",
            "awesome",
            "perfect",
            "happy",
            "delighted",
            "excited",
            "innovative",
        ]
        negative_words = [
            "bad",
            "terrible",
            "awful",
            "poor",
            "worst",
            "hate",
            "disappointed",
            "difficult",
            "problem",
            "issue",
            "error",
            "fail",
            "wrong",
        ]

        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        total = pos_count + neg_count
        if total == 0:
            sentiment = "neutral"
            score = 0.5
        else:
            score = pos_count / total
            if score > 0.6:
                sentiment = "positive"
            elif score < 0.4:
                sentiment = "negative"
            else:
                sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "score": round(score, 3),
            "positive_matches": pos_count,
            "negative_matches": neg_count,
        }

    def _analyze_characteristics(self, text: str) -> Dict[str, Any]:
        """Analyze text characteristics"""
        words = text.split()
        sentences = re.split(r"[.!?]+", text)

        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0

        # Average sentence length
        avg_sentence_length = len(words) / len(sentences) if sentences else 0

        # Exclamation and question marks
        exclamation_count = text.count("!")
        question_count = text.count("?")

        # Detect formality indicators
        first_person = len(re.findall(r"\b(I|we|us|our)\b", text, re.IGNORECASE))
        second_person = len(re.findall(r"\b(you|your)\b", text, re.IGNORECASE))

        return {
            "avg_word_length": round(avg_word_length, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "exclamations": exclamation_count,
            "questions": question_count,
            "first_person_usage": first_person,
            "second_person_usage": second_person,
            "formality_indicator": (
                "formal" if avg_word_length > 5 and first_person < 5 else "casual"
            ),
        }

    def _extract_key_phrases(self, text: str, num_phrases: int = 5) -> List[str]:
        """Extract key phrases from text"""
        # Split into sentences
        sentences = re.split(r"[.!?]+", text)

        # Get first few sentences as samples
        key_phrases = []
        for sentence in sentences[:num_phrases]:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Minimum length
                key_phrases.append(sentence[:200])  # Limit length

        return key_phrases
