import re
import logging

logger = logging.getLogger(__name__)

def check_password_strength(password: str) -> dict:
    """
    Check password strength and return detailed analysis
    
    Args:
        password (str): Password to analyze
        
    Returns:
        dict: Dictionary with strength score and details
    """
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password should be at least 8 characters long")
    
    if len(password) >= 12:
        score += 1
    
    # Character variety checks
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Password should contain at least one lowercase letter")
    
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Password should contain at least one uppercase letter")
    
    if re.search(r'\d', password):
        score += 1
    else:
        feedback.append("Password should contain at least one digit")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        feedback.append("Password should contain at least one special character")
    
    # Additional checks
    if len(set(password)) >= len(password) * 0.7:  # 70% unique characters
        score += 1
    
    # Common patterns to avoid
    common_patterns = [
        'password', '123456', 'qwerty', 'admin', 'user',
        'letmein', 'welcome', 'monkey', 'dragon', 'master'
    ]
    
    password_lower = password.lower()
    for pattern in common_patterns:
        if pattern in password_lower:
            score -= 1
            feedback.append(f"Avoid common patterns like '{pattern}'")
            break
    
    # Determine strength level
    if score <= 2:
        strength = "weak"
    elif score <= 4:
        strength = "fair"
    elif score <= 6:
        strength = "good"
    else:
        strength = "strong"
    
    return {
        "score": score,
        "strength": strength,
        "feedback": feedback,
        "length": len(password),
        "has_lowercase": bool(re.search(r'[a-z]', password)),
        "has_uppercase": bool(re.search(r'[A-Z]', password)),
        "has_digit": bool(re.search(r'\d', password)),
        "has_special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    }

def is_password_strong_enough(password: str, min_score: int = 4) -> bool:
    """
    Check if password meets minimum strength requirements
    
    Args:
        password (str): Password to check
        min_score (int): Minimum strength score required
        
    Returns:
        bool: True if password is strong enough
    """
    analysis = check_password_strength(password)
    return analysis["score"] >= min_score

def get_password_requirements() -> dict:
    """
    Get password requirements for user guidance
    
    Returns:
        dict: Password requirements
    """
    return {
        "min_length": 8,
        "recommended_length": 12,
        "required_chars": [
            "At least one lowercase letter (a-z)",
            "At least one uppercase letter (A-Z)",
            "At least one digit (0-9)",
            "At least one special character (!@#$%^&*(),.?\":{}|<>)"
        ],
        "avoid": [
            "Common words (password, admin, user, etc.)",
            "Sequential characters (123456, qwerty, etc.)",
            "Personal information (name, birthdate, etc.)"
        ],
        "tips": [
            "Use a mix of letters, numbers, and symbols",
            "Make it at least 8 characters long",
            "Avoid using the same password for multiple accounts",
            "Consider using a passphrase instead of a single word"
        ]
    } 