"""
Validation utilities for data validation and sanitization.
Pure functions for input validation and data cleaning.
"""

import re
from typing import Optional, List, Dict, Any
from pathlib import Path


def validate_filename(filename: str) -> bool:
    """
    Validate filename for security and compatibility.
    
    Args:
        filename: The filename to validate
        
    Returns:
        True if filename is valid, False otherwise
    """
    if not filename or len(filename) > 255:
        return False
    
    # Check for dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
    if any(char in filename for char in dangerous_chars):
        return False
    
    # Check for reserved names (Windows)
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_without_extension = Path(filename).stem.upper()
    if name_without_extension in reserved_names:
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing dangerous characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*\0]', '', filename)
    
    # Replace spaces and other characters
    filename = re.sub(r'[\\/ ]', '_', filename)
    
    # Limit length
    if len(filename) > 200:
        name = Path(filename).stem[:190]
        extension = Path(filename).suffix
        filename = f"{name}{extension}"
    
    return filename


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate file extension against allowed list.
    
    Args:
        filename: The filename to check
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.txt'])
        
    Returns:
        True if extension is allowed, False otherwise
    """
    file_extension = Path(filename).suffix.lower()
    return file_extension in [ext.lower() for ext in allowed_extensions]


def validate_file_size(size: int, max_size: int) -> bool:
    """
    Validate file size against maximum allowed size.
    
    Args:
        size: File size in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        True if size is within limit, False otherwise
    """
    return 0 < size <= max_size


def validate_language_code(language: Optional[str]) -> bool:
    """
    Validate ISO 639-1 language code.
    
    Args:
        language: Language code to validate
        
    Returns:
        True if valid, False otherwise
    """
    if language is None:
        return True
    
    # Check format (2 lowercase letters)
    if not isinstance(language, str) or len(language) != 2:
        return False
    
    return language.islower() and language.isalpha()


def validate_pagination_params(page: int, per_page: int) -> Dict[str, Any]:
    """
    Validate and normalize pagination parameters.
    
    Args:
        page: Page number
        per_page: Items per page
        
    Returns:
        Dictionary with validated parameters
    """
    # Ensure positive values
    page = max(1, page)
    per_page = max(1, min(per_page, 100))  # Cap at 100 items per page
    
    return {
        "page": page,
        "per_page": per_page,
        "offset": (page - 1) * per_page
    }


def validate_job_id(job_id: str) -> bool:
    """
    Validate job ID format (UUID).
    
    Args:
        job_id: Job ID to validate
        
    Returns:
        True if valid UUID format, False otherwise
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(job_id))


def validate_content_type(content_type: str, expected_types: List[str]) -> bool:
    """
    Validate HTTP content type.
    
    Args:
        content_type: Content type header value
        expected_types: List of expected content types
        
    Returns:
        True if content type is expected, False otherwise
    """
    # Extract main content type (ignore charset, etc.)
    main_type = content_type.split(';')[0].strip().lower()
    return main_type in [t.lower() for t in expected_types]


def clean_text_content(content: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        content: Text content to clean
        
    Returns:
        Cleaned text content
    """
    if not content:
        return ""
    
    # Remove null bytes and other control characters
    content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)
    
    # Normalize whitespace
    content = re.sub(r'\r\n', '\n', content)  # Windows line endings
    content = re.sub(r'\r', '\n', content)    # Mac line endings
    content = re.sub(r'\n{3,}', '\n\n', content)  # Excessive newlines
    
    # Trim whitespace
    content = content.strip()
    
    return content


def extract_metadata_from_filename(filename: str) -> Dict[str, Any]:
    """
    Extract useful metadata from filename.
    
    Args:
        filename: Original filename
        
    Returns:
        Dictionary with extracted metadata
    """
    path = Path(filename)
    
    metadata = {
        "original_name": filename,
        "name_without_extension": path.stem,
        "extension": path.suffix.lower(),
        "estimated_language": None,
        "document_type": None
    }
    
    # Try to detect language from filename
    language_patterns = {
        'en': r'(?i)(english|en_|_en|eng)',
        'fr': r'(?i)(french|fr_|_fr|fra)',
        'es': r'(?i)(spanish|es_|_es|spa)',
        'de': r'(?i)(german|de_|_de|deu)',
    }
    
    for lang, pattern in language_patterns.items():
        if re.search(pattern, filename):
            metadata["estimated_language"] = lang
            break
    
    # Try to detect document type from filename
    type_patterns = {
        'invoice': r'(?i)(invoice|facture|bill|receipt)',
        'contract': r'(?i)(contract|agreement|contrat)',
        'report': r'(?i)(report|rapport|analysis)',
        'manual': r'(?i)(manual|guide|handbook)',
    }
    
    for doc_type, pattern in type_patterns.items():
        if re.search(pattern, filename):
            metadata["document_type"] = doc_type
            break
    
    return metadata 