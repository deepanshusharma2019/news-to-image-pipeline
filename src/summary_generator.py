"""
Text Summary Generator
Creates informative summaries for news headlines.
"""

import re
import logging
from typing import Dict, List, Optional

class SummaryGenerator:
    """Generate contextual summaries for news headlines."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Keywords that help generate context
        self.context_keywords = {
            'arrest': ['law enforcement action', 'police operation', 'legal proceedings'],
            'protest': ['public demonstration', 'civic engagement', 'social movement'],
            'rally': ['public gathering', 'political assembly', 'community event'],
            'election': ['democratic process', 'voting procedures', 'political campaign'],
            'court': ['legal proceedings', 'judicial system', 'legal decision'],
            'government': ['official policy', 'administrative action', 'public governance'],
            'technology': ['technological advancement', 'digital innovation', 'tech development'],
            'economy': ['economic impact', 'financial market', 'business development'],
            'health': ['public health', 'medical advancement', 'healthcare system'],
            'climate': ['environmental impact', 'climate action', 'sustainability'],
            'sports': ['athletic competition', 'sporting event', 'recreational activity'],
            'entertainment': ['cultural event', 'media coverage', 'public performance']
        }
        
        # Location context
        self.location_context = {
            'london': 'United Kingdom capital city',
            'paris': 'French capital city', 
            'new york': 'US major metropolitan area',
            'washington': 'US capital region',
            'beijing': 'Chinese capital city',
            'tokyo': 'Japanese capital city',
            'berlin': 'German capital city',
            'moscow': 'Russian capital city'
        }
    
    def generate_summary(self, headline: str) -> str:
        """Generate a contextual summary for a news headline."""
        try:
            # Clean and analyze headline
            clean_headline = self._clean_headline(headline)
            words = clean_headline.lower().split()
            
            # Extract key information
            numbers = self._extract_numbers(clean_headline)
            locations = self._extract_locations(clean_headline)
            context_type = self._determine_context_type(words)
            
            # Build summary components
            summary_parts = []
            
            # Add context about what this represents
            if context_type:
                context_desc = self.context_keywords.get(context_type, ['significant news event'])
                summary_parts.append(f"This headline reports on a {context_desc[0]}")
            
            # Add numerical context
            if numbers:
                if any(num > 100 for num in numbers):
                    summary_parts.append("involving a significant number of people")
                elif any(num > 10 for num in numbers):
                    summary_parts.append("affecting multiple individuals")
            
            # Add location context
            if locations:
                for location in locations:
                    loc_context = self.location_context.get(location.lower())
                    if loc_context:
                        summary_parts.append(f"taking place in {location} ({loc_context})")
                    else:
                        summary_parts.append(f"occurring in {location}")
            
            # Add impact assessment
            impact = self._assess_impact(clean_headline, numbers)
            if impact:
                summary_parts.append(impact)
            
            # Add temporal context
            temporal = self._get_temporal_context(words)
            if temporal:
                summary_parts.append(temporal)
            
            # Combine into coherent summary
            if summary_parts:
                summary = ". ".join(summary_parts) + "."
                # Clean up grammar
                summary = summary.replace("a involving", "involving")
                summary = summary.replace("a affecting", "affecting")
                return summary
            else:
                # Fallback summary
                return f"Breaking news: {clean_headline}. This developing story represents a significant current event that may have broader implications for the affected community and stakeholders."
                
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return f"News Update: {headline}. This story is part of ongoing current events coverage."
    
    def _clean_headline(self, headline: str) -> str:
        """Clean and normalize headline text."""
        # Remove extra quotes and clean up
        clean = headline.strip().strip('"').strip("'")
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean)
        return clean
    
    def _extract_numbers(self, text: str) -> List[int]:
        """Extract numerical values from text."""
        numbers = []
        # Find written numbers and digits
        number_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'dozen': 12, 'hundred': 100, 'thousand': 1000, 'million': 1000000
        }
        
        words = text.lower().split()
        for word in words:
            # Check for digits
            if word.isdigit():
                numbers.append(int(word))
            # Check for number words
            elif word in number_words:
                numbers.append(number_words[word])
            # Check for numbers with commas
            elif re.match(r'^\d{1,3}(,\d{3})*$', word):
                numbers.append(int(word.replace(',', '')))
        
        return numbers
    
    def _extract_locations(self, text: str) -> List[str]:
        """Extract location names from text."""
        locations = []
        
        # Common location patterns (capitalized words)
        words = text.split()
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2:
                # Check if it's likely a location
                if word.lower() in self.location_context:
                    locations.append(word)
                # Check for "in [Location]" pattern
                elif i > 0 and words[i-1].lower() == 'in':
                    locations.append(word)
        
        return locations
    
    def _determine_context_type(self, words: List[str]) -> Optional[str]:
        """Determine the type of news context."""
        for word in words:
            if word in self.context_keywords:
                return word
        
        # Check for variations
        word_variations = {
            'arrested': 'arrest',
            'protesting': 'protest',
            'rallying': 'rally',
            'voting': 'election',
            'technological': 'technology',
            'economic': 'economy'
        }
        
        for word in words:
            if word in word_variations:
                return word_variations[word]
        
        return None
    
    def _assess_impact(self, headline: str, numbers: List[int]) -> Optional[str]:
        """Assess the potential impact of the news."""
        headline_lower = headline.lower()
        
        # High impact indicators
        high_impact_words = ['breaking', 'major', 'massive', 'unprecedented', 'historic', 'crisis']
        if any(word in headline_lower for word in high_impact_words):
            return "This appears to be a high-impact news event with potential widespread implications"
        
        # Large number impact
        if numbers and max(numbers) > 1000:
            return "The scale of this event suggests significant community or regional impact"
        elif numbers and max(numbers) > 100:
            return "This event involves substantial participation or impact"
        
        # Policy/government impact
        policy_words = ['government', 'policy', 'law', 'legislation', 'regulation']
        if any(word in headline_lower for word in policy_words):
            return "This development may have policy implications and affect regulatory frameworks"
        
        return None
    
    def _get_temporal_context(self, words: List[str]) -> Optional[str]:
        """Add temporal context to the summary."""
        temporal_words = {
            'breaking': "This is a developing story with ongoing updates expected",
            'continues': "This represents an ongoing situation",
            'begins': "This marks the start of a new development",
            'ends': "This concludes a significant period or event",
            'announces': "This is a recent official announcement",
            'reports': "This information has been recently disclosed"
        }
        
        for word in words:
            if word in temporal_words:
                return temporal_words[word]
        
        return "This story is part of current news coverage"
