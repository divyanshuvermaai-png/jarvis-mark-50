import re
import subprocess
from .errors import ContactAmbiguousError, ContactNotFoundError


def is_phone_number(contact: str) -> bool:
    """Checks if a contact identifier is a numeric phone number."""
    cleaned = re.sub(r'[\s\-\(\)\+]', '', contact.strip())
    return cleaned.isdigit() and len(cleaned) >= 7


class ContactResolver:
    """Resolves names against macOS local Contacts to prevent ambiguous automated actions."""
    
    def __init__(self):
        pass

    def check_ambiguity(self, name: str) -> str:
        """
        Queries the macOS Contacts app to see how many people match the name.
        If > 1, raises ContactAmbiguousError.
        Returns the best matched name to pass to WhatsApp.
        """
        # If target is already a phone number, bypass Contacts lookup
        if is_phone_number(name):
            cleaned = re.sub(r'[\s\-\(\)]', '', name.strip())
            return cleaned

        # AppleScript to find contacts whose name contains the query
        script = f"""
        tell application "Contacts"
            set matching_people to every person whose name contains "{name}"
            set nameList to {{}}
            repeat with p in matching_people
                set end of nameList to name of p
            end repeat
            return nameList
        end tell
        """
        try:
            res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            if res.returncode != 0:
                # If Contacts app is blocking access or throws an error, fallback to exact string 
                # to not block the pipeline if they haven't synced Contacts, but we log a warning.
                return name
                
            output = res.stdout.strip()
            if not output:
                # No contacts found in macOS Contacts. They might only exist in WhatsApp.
                # We return the exact name, relying on WhatsApp's internal search.
                return name
                
            # AppleScript returns a comma-separated list like "John Doe, John Smith"
            names = [n.strip() for n in output.split(",") if n.strip()]
            
            # Exact match check
            exact_matches = [n for n in names if n.lower() == name.lower()]
            if len(exact_matches) == 1:
                return exact_matches[0]
                
            if len(names) > 1:
                raise ContactAmbiguousError(f"Found multiple contacts for '{name}': {names}")
                
            return names[0]
            
        except Exception as e:
            if isinstance(e, ContactAmbiguousError):
                raise e
            return name
