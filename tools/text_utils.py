"""
Example Python tool functions for ADK.

These functions can be called by agents using Python tool type.
"""


def summarize(text: str, max_length: int = 100) -> dict:
    """
    Summarize text to a maximum length.
    
    Args:
        text: Text to summarize
        max_length: Maximum length of summary
        
    Returns:
        Dict with summary and metadata
    """
    if len(text) <= max_length:
        return {
            "summary": text,
            "original_length": len(text),
            "summary_length": len(text),
            "truncated": False
        }
    
    # Simple truncation with ellipsis
    summary = text[:max_length-3] + "..."
    
    return {
        "summary": summary,
        "original_length": len(text),
        "summary_length": len(summary),
        "truncated": True
    }


def count_words(text: str) -> dict:
    """
    Count words in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dict with word count and statistics
    """
    words = text.split()
    
    return {
        "word_count": len(words),
        "character_count": len(text),
        "line_count": text.count('\n') + 1,
        "average_word_length": sum(len(w) for w in words) / len(words) if words else 0
    }


def extract_keywords(text: str, max_keywords: int = 5) -> dict:
    """
    Extract keywords from text (simple frequency-based).
    
    Args:
        text: Text to analyze
        max_keywords: Maximum number of keywords to return
        
    Returns:
        Dict with keywords and frequencies
    """
    # Simple word frequency analysis
    words = text.lower().split()
    
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
    words = [w for w in words if w not in stop_words and len(w) > 2]
    
    # Count frequencies
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    
    # Get top keywords
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    keywords = [{"word": word, "frequency": count} for word, count in sorted_words[:max_keywords]]
    
    return {
        "keywords": keywords,
        "total_unique_words": len(freq),
        "total_words_analyzed": len(words)
    }
