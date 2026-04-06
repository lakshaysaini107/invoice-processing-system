import re
from typing import Dict, Any, List
from backend.core.logging import logger
from backend.utils.regex_utils import REGEX_PATTERNS


class NEREngine:
    """Extract named entities (vendors, amounts, dates) using NLP"""

    def __init__(self):
        # Load spaCy model for NER
        try:
            import spacy

            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            logger.warning(
                "spaCy runtime or model not found. Install spaCy and "
                "download en_core_web_sm to enable NLP-based NER."
            )
            self.nlp = None

    async def extract_entities(
        self,
        raw_text: str,
        extracted_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract and validate entities:
        - Organizations (vendors)
        - Persons (contacts)
        - Amounts
        - Dates
        - Locations
        """
        
        entities = {
            "vendors": [],
            "dates": [],
            "amounts": [],
            "contacts": [],
            "locations": []
        }
        
        try:
            if self.nlp:
                # Use spaCy NER
                doc = self.nlp(raw_text)
                
                for ent in doc.ents:
                    if ent.label_ == "ORG":
                        entities["vendors"].append({
                            "name": ent.text,
                            "confidence": 0.8,
                            "type": "organization"
                        })
                    elif ent.label_ == "PERSON":
                        entities["contacts"].append({
                            "name": ent.text,
                            "confidence": 0.7,
                            "type": "person"
                        })
                    elif ent.label_ == "GPE":
                        entities["locations"].append({
                            "name": ent.text,
                            "confidence": 0.8,
                            "type": "location"
                        })
            
            # Regex-based extraction for amounts
            amounts = re.findall(REGEX_PATTERNS["amount"], raw_text)
            for amount in amounts:
                try:
                    # Basic cleanup for amount string
                    clean_amount = amount.replace(',', '').replace('₹', '').replace('Rs.', '').strip()
                    value = float(clean_amount)
                    entities["amounts"].append({
                        "value": value,
                        "text": amount,
                        "confidence": 0.85
                    })
                except:
                    pass
            
            # Regex-based extraction for dates
            dates = re.findall(REGEX_PATTERNS["date"], raw_text)
            for date_str in dates:
                entities["dates"].append({
                    "date_string": date_str,
                    "confidence": 0.7
                })
            
            logger.info(f"NER extraction: {len(entities['vendors'])} vendors, "
                       f"{len(entities['amounts'])} amounts, {len(entities['dates'])} dates")
            
            return entities
            
        except Exception as e:
            logger.error(f"NER extraction error: {str(e)}")
            return entities
