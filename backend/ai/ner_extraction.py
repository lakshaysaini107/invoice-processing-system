from typing import Any, Dict, List
from backend.core.logging import logger

HAS_SPACY = False
nlp = None
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        HAS_SPACY = True
    except Exception:
        HAS_SPACY = False
except ImportError:
    HAS_SPACY = False


class NERExtractor:
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        if not text:
            return {"organizations": [], "persons": [], "locations": [], "dates": []}

        if HAS_SPACY and nlp:
            try:
                doc = nlp(text[:10000])
                orgs = set()
                persons = set()
                gpes = set()
                dates = set()
                for ent in doc.ents:
                    if ent.label_ == "ORG":
                        orgs.add(ent.text.strip())
                    elif ent.label_ == "PERSON":
                        persons.add(ent.text.strip())
                    elif ent.label_ in ["GPE", "LOC"]:
                        gpes.add(ent.text.strip())
                    elif ent.label_ == "DATE":
                        dates.add(ent.text.strip())

                return {
                    "organizations": list(orgs)[:10],
                    "persons": list(persons)[:10],
                    "locations": list(gpes)[:10],
                    "dates": list(dates)[:10],
                }
            except Exception as exc:
                logger.warning(f"spaCy NER extraction error: {exc}")

        return {"organizations": [], "persons": [], "locations": [], "dates": []}


ner_extractor = NERExtractor()
