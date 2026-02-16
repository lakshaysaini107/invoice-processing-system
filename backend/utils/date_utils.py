from datetime import datetime
from typing import Optional
import re

def parse_date(date_string: str) -> Optional[str]:
    """Parse date in multiple formats and return YYYY-MM-DD"""
    if not date_string:
        return None
    
    date_string = date_string.strip()
    
    # Try common formats
    formats = [
        "%Y-%m-%d",      # 2024-01-15
        "%d-%m-%Y",      # 15-01-2024
        "%m-%d-%Y",      # 01-15-2024
        "%d/%m/%Y",      # 15/01/2024
        "%m/%d/%Y",      # 01/15/2024
        "%Y/%m/%d",      # 2024/01/15
        "%d.%m.%Y",      # 15.01.2024
        "%d %b %Y",      # 15 Jan 2024
        "%d %B %Y",      # 15 January 2024
        "%b %d, %Y",     # Jan 15, 2024
        "%B %d, %Y",     # January 15, 2024
        "%d-%b-%Y",      # 15-Jan-2024
        "%d-%b-%y",      # 15-Jan-24
        "%d-%B-%Y",      # 15-January-2024
        "%d-%B-%y",      # 15-January-24
        "%d/%b/%Y",      # 15/Jan/2024
        "%d/%b/%y",      # 15/Jan/24
        "%d/%B/%Y",      # 15/January/2024
        "%d/%B/%y",      # 15/January/24
        "%d %b %y",      # 15 Jan 24
        "%d %B %y",      # 15 January 24
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_string, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None

def validate_date(date_string: str) -> bool:
    """Check if date string is valid"""
    return parse_date(date_string) is not None

def get_date_range(start_date: str, end_date: str) -> tuple:
    """Get date range as datetime objects"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return start, end

def is_date_after_today(date_string: str) -> bool:
    """Check if date is in future"""
    try:
        date = datetime.strptime(parse_date(date_string), "%Y-%m-%d")
        return date > datetime.now()
    except:
        return False

def extract_dates_from_text(text: str) -> list:
    """Extract all possible dates from text"""
    dates = []
    
    # Pattern for DD-MM-YYYY, DD/MM/YYYY, etc.
    pattern = r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"
    matches = re.findall(pattern, text)
    
    for match in matches:
        parsed = parse_date(match)
        if parsed:
            dates.append(parsed)
    
    return list(set(dates))  # Remove duplicates
