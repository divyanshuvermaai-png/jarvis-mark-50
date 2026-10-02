"""
J.A.R.V.I.S. WhatsApp Agent - Contact Resolver
Resolves natural-language contact mentions to verified WhatsApp contacts using
fuzzy matching, nickname mapping, phonetic normalization, and ambiguity detection.
"""
import re
import difflib
import subprocess
import logging
from typing import List, Optional, Tuple, Dict
from .models import ContactMatch

logger = logging.getLogger("jarvis.whatsapp.contact_resolver")


def is_phone_number(contact: str) -> bool:
    """Checks if a contact identifier is a numeric phone number."""
    cleaned = re.sub(r'[\s\-\(\)\+]', '', contact.strip())
    return cleaned.isdigit() and len(cleaned) >= 7


def normalize_phone(phone: str) -> str:
    """Normalizes phone number to clean E.164-like digits string."""
    cleaned = re.sub(r'[\s\-\(\)]', '', phone.strip())
    return cleaned


def soundex(text: str) -> str:
    """Simple soundex algorithm for phonetic matching of names from ASR speech."""
    text = re.sub(r'[^a-zA-Z]', '', text.upper())
    if not text:
        return "0000"
    first_letter = text[0]
    mapping = {
        'B': '1', 'F': '1', 'P': '1', 'V': '1',
        'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6'
    }
    encoded = [first_letter]
    prev = mapping.get(first_letter, '0')
    for char in text[1:]:
        code = mapping.get(char, '0')
        if code != '0' and code != prev:
            encoded.append(code)
            prev = code
        elif code == '0':
            prev = '0'
    res = "".join(encoded) + "0000"
    return res[:4]


class ContactResolver:
    """
    Intelligent contact resolution engine.
    Ensures J.A.R.V.I.S. never sends or calls an arbitrary contact without confidence.
    """

    NICKNAMES: Dict[str, List[str]] = {
        "mom": ["mom", "mother", "mummy", "maa", "mum"],
        "dad": ["dad", "father", "papa", "pop", "pappa"],
        "bro": ["brother", "bhai", "bro"],
        "sis": ["sister", "didi", "sis"],
        "wife": ["wife", "partner", "spouse"],
        "boss": ["boss", "manager", "lead"]
    }

    def __init__(self, contact_cache: Optional[List[str]] = None):
        self._cache = contact_cache or []
        self._phone_map: Dict[str, str] = {}
        self._load_fallback_contacts()
        self._load_system_contacts()

    def _load_fallback_contacts(self):
        """Initial baseline contacts if none provided."""
        if not self._cache:
            self._cache = [
                "Rahul Sharma",
                "Mom",
                "Dad",
                "Ankit",
                "Priya",
                "Divyanshu Verma",
                "Subham",
                "Alex Smith",
                "Alex Johnson"
            ]

    def _load_system_contacts(self):
        """Loads contacts and their phone numbers from macOS Contacts app."""
        try:
            script = """
            tell application "Contacts"
                set res to {}
                repeat with p in people
                    set pName to name of p
                    set pPhone to ""
                    try
                        set pPhone to value of first item of phones of p
                    end try
                    if length of pName > 0 then
                        set end of res to (pName & "||" & pPhone)
                    end if
                end repeat
                return res
            end tell
            """
            res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                for item in res.stdout.strip().split(','):
                    item = item.strip()
                    if not item:
                        continue
                    if '||' in item:
                        n, p = item.split('||', 1)
                        n = n.strip()
                        p = p.strip()
                        if n and n not in self._cache:
                            self._cache.append(n)
                            if p:
                                self._phone_map[n.lower()] = p
        except Exception as e:
            logger.debug(f"Could not load macOS system contacts: {e}")

    def set_contacts(self, contacts: List[str]):
        """Sets or refreshes known contacts."""
        self._cache = contacts

    def query_macos_contacts(self, query: str) -> List[Tuple[str, Optional[str]]]:
        """Queries local macOS Contacts app via AppleScript for system contacts with phones."""
        tokens = [query.strip()]
        first_word = query.strip().split()[0]
        if first_word and first_word not in tokens:
            tokens.append(first_word)

        results = []
        for tok in tokens:
            safe_tok = tok.replace('\\', '\\\\').replace('"', '\\"')
            script = f"""
            tell application "Contacts"
                set matching_people to (every person whose name contains "{safe_tok}")
                set contactList to {{}}
                repeat with p in matching_people
                    set pName to name of p
                    set pPhone to ""
                    try
                        set pPhone to value of first item of phones of p
                    end try
                    set end of contactList to (pName & "||" & pPhone)
                end repeat
                return contactList
            end tell
            """
            try:
                res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
                if res.returncode == 0 and res.stdout.strip():
                    for item in res.stdout.strip().split(','):
                        item = item.strip()
                        if not item:
                            continue
                        if '||' in item:
                            n, p = item.split('||', 1)
                            results.append((n.strip(), p.strip() if p.strip() else None))
                        else:
                            results.append((item, None))
            except Exception as e:
                logger.debug(f"macOS Contacts query failed: {e}")
            if results:
                break
        return results

    def find_matches(self, name_query: str) -> List[ContactMatch]:
        """
        Finds candidate contact matches using exact, nickname, fuzzy, and phonetic matching.
        Returns a sorted list of ContactMatch objects ordered by confidence descending.
        """
        query = name_query.strip()
        if not query:
            return []

        # 1. Direct Phone Number check
        if is_phone_number(query):
            norm = normalize_phone(query)
            return [ContactMatch(
                name=norm,
                phone=norm,
                match_score=1.0,
                is_exact=True,
                source="phone_number",
                raw_query=query
            )]

        # 2. Nickname resolution
        query_lower = query.lower()
        expanded_queries = [query_lower]
        for canonical, aliases in self.NICKNAMES.items():
            if query_lower in aliases:
                expanded_queries.append(canonical)
                expanded_queries.extend(aliases)
                break

        # Pool contacts from cache and optional OS query
        os_contacts = self.query_macos_contacts(query)
        for n, p in os_contacts:
            if p:
                self._phone_map[n.lower()] = p

        cache_names = [c.name if hasattr(c, 'name') else str(c) for c in self._cache]
        os_names = [n for n, p in os_contacts]
        pool = list(dict.fromkeys(cache_names + os_names))
        if not pool:
            # Fallback to query itself if no pool available
            return [ContactMatch(name=query, match_score=0.7, is_exact=False, raw_query=query)]

        matches: List[ContactMatch] = []
        q_soundex = soundex(query)

        for contact in pool:
            c_lower = contact.lower()
            c_soundex = soundex(contact.split()[0] if contact else "")
            c_phone = self._phone_map.get(c_lower)

            # Exact match
            if c_lower == query_lower or any(c_lower == eq for eq in expanded_queries):
                matches.append(ContactMatch(
                    name=contact,
                    phone=c_phone,
                    match_score=1.0,
                    is_exact=True,
                    source="exact_match",
                    raw_query=query
                ))
                continue

            # First name exact match (e.g. "Rahul" matching "Rahul Sharma")
            first_name = contact.split()[0].lower() if contact else ""
            if first_name == query_lower:
                matches.append(ContactMatch(
                    name=contact,
                    phone=c_phone,
                    match_score=0.92,
                    is_exact=False,
                    source="first_name_match",
                    raw_query=query
                ))
                continue

            # Substring / Prefix match
            if query_lower in c_lower:
                matches.append(ContactMatch(
                    name=contact,
                    phone=c_phone,
                    match_score=0.88,
                    is_exact=False,
                    source="substring_match",
                    raw_query=query
                ))
                continue

            # Fuzzy ratio match
            ratio = difflib.SequenceMatcher(None, query_lower, c_lower).ratio()
            # Also compare against first name
            fn_ratio = difflib.SequenceMatcher(None, query_lower, first_name).ratio()
            best_ratio = max(ratio, fn_ratio)

            # Phonetic bonus if soundex matches
            if q_soundex == c_soundex and best_ratio >= 0.6:
                best_ratio = min(1.0, best_ratio + 0.15)

            if best_ratio >= 0.70:
                matches.append(ContactMatch(
                    name=contact,
                    phone=c_phone,
                    match_score=round(best_ratio, 2),
                    is_exact=False,
                    source="fuzzy_match",
                    raw_query=query
                ))

        # Sort matches by score descending
        matches.sort(key=lambda m: m.match_score, reverse=True)
        return matches

    def resolve(self, name_query: str) -> Tuple[Optional[ContactMatch], List[ContactMatch]]:
        """
        Resolves a contact query.
        Returns: (resolved_contact, ambiguous_candidates)
        - If resolved_contact is not None: unambiguous single match found.
        - If ambiguous_candidates is non-empty and resolved_contact is None: multiple matches found.
        - If both are None/empty: no match found.
        """
        matches = self.find_matches(name_query)
        if not matches:
            return None, []

        # Exact match single candidate
        if matches[0].is_exact:
            return matches[0], []

        # Check if top match is overwhelmingly better than second match
        if len(matches) == 1:
            if matches[0].match_score >= 0.75:
                return matches[0], []
            return None, matches

        # Multiple matches
        top_score = matches[0].match_score
        close_matches = [m for m in matches if m.match_score >= (top_score - 0.08) and m.match_score >= 0.75]

        if len(close_matches) == 1:
            return close_matches[0], []

        # Ambiguity exists
        return None, close_matches
