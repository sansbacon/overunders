"""Content moderation and filtering utilities."""
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from flask import current_app
import openai
from app import db


logger = logging.getLogger(__name__)


class ContentModerationResult:
    """Result of content moderation check."""
    
    def __init__(self, is_safe: bool, confidence: float = 1.0, 
                 flagged_words: List[str] = None, categories: List[str] = None,
                 reason: str = None):
        self.is_safe = is_safe
        self.confidence = confidence
        self.flagged_words = flagged_words or []
        self.categories = categories or []
        self.reason = reason or ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'is_safe': self.is_safe,
            'confidence': self.confidence,
            'flagged_words': self.flagged_words,
            'categories': self.categories,
            'reason': self.reason
        }


class ContentFilter:
    """Content filtering and moderation service."""
    
    # Basic profanity word list (expandable)
    PROFANITY_WORDS = {
        # Mild profanity
        'mild': [
            'damn', 'hell', 'crap', 'piss', 'ass', 'bastard', 'bitch'
        ],
        # Strong profanity
        'strong': [
            'fuck', 'shit', 'motherfucker', 'asshole', 'dickhead', 'pussy'
        ],
        # Hate speech and slurs (partial list - should be expanded)
        'hate': [
            'nigger', 'faggot', 'retard', 'spic', 'chink', 'kike', 'wetback'
        ]
    }
    
    # Spam patterns
    SPAM_PATTERNS = [
        r'(?i)\b(?:buy|sell|cheap|discount|offer|deal|money|cash|prize|winner|free|click|visit|website|link)\b.*(?:now|today|limited|urgent)',
        r'(?i)\b(?:viagra|cialis|pharmacy|pills|medication|drugs)\b',
        r'(?i)\b(?:casino|gambling|poker|lottery|jackpot|betting)\b',
        r'(?i)\b(?:make money|work from home|earn \$|guaranteed income)\b',
        r'(?i)\b(?:weight loss|lose weight|diet pills|fat burner)\b'
    ]
    
    # Inappropriate content patterns
    INAPPROPRIATE_PATTERNS = [
        r'(?i)\b(?:sex|porn|xxx|adult|nude|naked|escort|prostitute)\b',
        r'(?i)\b(?:kill|murder|suicide|death|violence|weapon|gun|bomb)\b',
        r'(?i)\b(?:drug|cocaine|heroin|marijuana|weed|meth|crack)\b'
    ]
    
    def __init__(self):
        """Initialize content filter."""
        # Don't access current_app during init - will be set when needed
        self.ai_moderation_enabled = None
        self.openai_api_key = None
        
        # Compile regex patterns for efficiency
        self.spam_regex = [re.compile(pattern) for pattern in self.SPAM_PATTERNS]
        self.inappropriate_regex = [re.compile(pattern) for pattern in self.INAPPROPRIATE_PATTERNS]
    
    def _ensure_config_loaded(self):
        """Ensure configuration is loaded from Flask app context."""
        if self.ai_moderation_enabled is None:
            try:
                self.ai_moderation_enabled = current_app.config.get('AI_MODERATION_ENABLED', False)
                self.openai_api_key = current_app.config.get('OPENAI_API_KEY')
            except RuntimeError:
                # No app context available, use defaults
                self.ai_moderation_enabled = False
                self.openai_api_key = None
    
    def check_profanity(self, text: str) -> ContentModerationResult:
        """Check text for profanity and inappropriate language.
        
        Args:
            text (str): Text to check
            
        Returns:
            ContentModerationResult: Moderation result
        """
        if not text:
            return ContentModerationResult(is_safe=True)
        
        text_lower = text.lower()
        flagged_words = []
        categories = []
        severity_score = 0
        
        # Check against profanity word lists
        for category, words in self.PROFANITY_WORDS.items():
            for word in words:
                if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                    flagged_words.append(word)
                    categories.append(category)
                    
                    # Assign severity scores
                    if category == 'mild':
                        severity_score += 1
                    elif category == 'strong':
                        severity_score += 3
                    elif category == 'hate':
                        severity_score += 5
        
        # Check for spam patterns
        for pattern in self.spam_regex:
            if pattern.search(text):
                categories.append('spam')
                severity_score += 2
                break
        
        # Check for inappropriate content
        for pattern in self.inappropriate_regex:
            if pattern.search(text):
                categories.append('inappropriate')
                severity_score += 3
                break
        
        # Determine if content is safe based on severity
        is_safe = severity_score < 3  # Threshold for blocking content
        confidence = min(1.0, severity_score / 10.0)  # Confidence based on severity
        
        reason = ""
        if not is_safe:
            if 'hate' in categories:
                reason = "Contains hate speech or slurs"
            elif 'strong' in categories:
                reason = "Contains strong profanity"
            elif 'inappropriate' in categories:
                reason = "Contains inappropriate content"
            elif 'spam' in categories:
                reason = "Appears to be spam"
            else:
                reason = "Contains inappropriate language"
        
        return ContentModerationResult(
            is_safe=is_safe,
            confidence=confidence,
            flagged_words=flagged_words,
            categories=list(set(categories)),
            reason=reason
        )
    
    def check_ai_moderation(self, text: str) -> ContentModerationResult:
        """Check text using OpenAI's moderation API.
        
        Args:
            text (str): Text to check
            
        Returns:
            ContentModerationResult: Moderation result
        """
        self._ensure_config_loaded()
        if not self.ai_moderation_enabled or not self.openai_api_key:
            return ContentModerationResult(is_safe=True, reason="AI moderation disabled")
        
        try:
            # Set up OpenAI API key
            openai.api_key = self.openai_api_key
            
            # Use OpenAI's moderation endpoint
            response = openai.Moderation.create(input=text)
            result = response['results'][0]
            
            is_safe = not result['flagged']
            categories = []
            flagged_categories = []
            
            # Extract flagged categories
            for category, flagged in result['categories'].items():
                if flagged:
                    categories.append(category)
                    flagged_categories.append(category)
            
            # Get confidence scores
            category_scores = result.get('category_scores', {})
            max_score = max(category_scores.values()) if category_scores else 0
            
            reason = ""
            if not is_safe:
                reason = f"AI detected: {', '.join(flagged_categories)}"
            
            return ContentModerationResult(
                is_safe=is_safe,
                confidence=max_score,
                flagged_words=[],  # AI doesn't provide specific words
                categories=categories,
                reason=reason
            )
            
        except Exception as e:
            logger.error(f"AI moderation error: {e}")
            # Fall back to safe result if AI fails
            return ContentModerationResult(is_safe=True, reason=f"AI moderation failed: {str(e)}")
    
    def moderate_content(self, text: str, content_type: str = "general") -> ContentModerationResult:
        """Perform comprehensive content moderation.
        
        Args:
            text (str): Text to moderate
            content_type (str): Type of content (contest, league, question, etc.)
            
        Returns:
            ContentModerationResult: Combined moderation result
        """
        if not text or not text.strip():
            return ContentModerationResult(is_safe=True)
        
        self._ensure_config_loaded()
        
        # Start with basic profanity check
        basic_result = self.check_profanity(text)
        
        # If AI moderation is enabled, also check with AI
        if self.ai_moderation_enabled:
            ai_result = self.check_ai_moderation(text)
            
            # Combine results - content is safe only if both checks pass
            is_safe = basic_result.is_safe and ai_result.is_safe
            confidence = max(basic_result.confidence, ai_result.confidence)
            flagged_words = basic_result.flagged_words
            categories = list(set(basic_result.categories + ai_result.categories))
            
            # Combine reasons
            reasons = []
            if basic_result.reason:
                reasons.append(f"Basic filter: {basic_result.reason}")
            if ai_result.reason and not ai_result.is_safe:
                reasons.append(f"AI filter: {ai_result.reason}")
            reason = "; ".join(reasons)
            
            return ContentModerationResult(
                is_safe=is_safe,
                confidence=confidence,
                flagged_words=flagged_words,
                categories=categories,
                reason=reason
            )
        else:
            return basic_result
    
    def is_spam(self, text: str) -> bool:
        """Quick check if text appears to be spam.
        
        Args:
            text (str): Text to check
            
        Returns:
            bool: True if text appears to be spam
        """
        if not text:
            return False
        
        for pattern in self.spam_regex:
            if pattern.search(text):
                return True
        
        return False
    
    def clean_text(self, text: str) -> str:
        """Clean text by removing or replacing inappropriate content.
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return text
        
        cleaned = text
        
        # Replace mild profanity with asterisks
        for word in self.PROFANITY_WORDS['mild']:
            pattern = r'\b' + re.escape(word) + r'\b'
            replacement = '*' * len(word)
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        return cleaned


# Global content filter instance
content_filter = ContentFilter()


def moderate_text(text: str, content_type: str = "general") -> ContentModerationResult:
    """Convenience function for content moderation.
    
    Args:
        text (str): Text to moderate
        content_type (str): Type of content
        
    Returns:
        ContentModerationResult: Moderation result
    """
    return content_filter.moderate_content(text, content_type)


def is_content_safe(text: str, content_type: str = "general") -> bool:
    """Quick check if content is safe.
    
    Args:
        text (str): Text to check
        content_type (str): Type of content
        
    Returns:
        bool: True if content is safe
    """
    result = moderate_text(text, content_type)
    return result.is_safe


def clean_content(text: str) -> str:
    """Clean content by removing inappropriate elements.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    return content_filter.clean_text(text)
