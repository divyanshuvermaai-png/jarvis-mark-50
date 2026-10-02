"""
Notes Plugin for J.A.R.V.I.S.
Quick note-taking — saves notes to ~/.jarvis_system/notes/
"""
import os
import json
from datetime import datetime
import sys
sys.path.insert(0, '..')
from plugin_system import PluginBase


class NotesPlugin(PluginBase):
    name = "notes"
    description = "Take, list, search, and delete quick notes"
    version = "1.0.0"
    commands = [
        'take a note', 'note that', 'save a note', 'write a note',
        'show my notes', 'list notes', 'read my notes',
        'delete note', 'clear notes', 'search notes', 'find note'
    ]
    
    def __init__(self, jarvis_context=None):
        super().__init__(jarvis_context)
        self.notes_dir = os.path.expanduser('~/.jarvis_system/notes')
        os.makedirs(self.notes_dir, exist_ok=True)
        self.notes_file = os.path.join(self.notes_dir, 'notes.json')
        if not os.path.exists(self.notes_file):
            with open(self.notes_file, 'w') as f:
                json.dump([], f)
    
    def execute(self, message, params=None):
        import re
        msg = message.lower().strip()
        
        if any(k in msg for k in ['show my notes', 'list notes', 'read my notes']):
            return self._list_notes()
        
        if 'clear notes' in msg or 'delete all notes' in msg:
            return self._clear_notes()
        
        if 'delete note' in msg:
            match = re.search(r'delete note\s*#?(\d+)', msg)
            if match:
                return self._delete_note(int(match.group(1)))
            return {'success': False, 'response': 'Which note should I delete, sir? Specify the note number.'}
        
        if any(k in msg for k in ['search notes', 'find note']):
            match = re.search(r'(?:search notes|find note)\s+(?:for\s+)?(.+)', msg)
            if match:
                return self._search_notes(match.group(1).strip())
            return {'success': False, 'response': 'What should I search for in your notes, sir?'}
        
        # Save a note
        match = re.search(r'(?:take a note|note that|save a note|write a note)\s*[:\-]?\s*(.+)', msg)
        if match:
            return self._save_note(match.group(1).strip())
        
        return {'success': False, 'response': "What would you like me to note, sir?"}
    
    def _load_notes(self):
        with open(self.notes_file, 'r') as f:
            return json.load(f)
    
    def _save_notes(self, notes):
        with open(self.notes_file, 'w') as f:
            json.dump(notes, f, indent=2)
    
    def _save_note(self, content):
        notes = self._load_notes()
        note = {
            'id': len(notes) + 1,
            'content': content,
            'created': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }
        notes.append(note)
        self._save_notes(notes)
        return {
            'success': True,
            'response': f"📝 Note #{note['id']} saved: \"{content}\""
        }
    
    def _list_notes(self):
        notes = self._load_notes()
        if not notes:
            return {'success': True, 'response': "You have no notes, sir. Your mind is clear."}
        
        response = f"📋 **Your Notes ({len(notes)})**\n\n"
        for n in notes[-10:]:  # Show last 10
            response += f"**#{n['id']}** ({n['created']}): {n['content']}\n"
        
        if len(notes) > 10:
            response += f"\n_...and {len(notes) - 10} more notes._"
        
        return {'success': True, 'response': response}
    
    def _delete_note(self, note_id):
        notes = self._load_notes()
        original = len(notes)
        notes = [n for n in notes if n['id'] != note_id]
        if len(notes) == original:
            return {'success': False, 'response': f"Note #{note_id} not found, sir."}
        self._save_notes(notes)
        return {'success': True, 'response': f"🗑️ Note #{note_id} deleted."}
    
    def _clear_notes(self):
        self._save_notes([])
        return {'success': True, 'response': "All notes have been cleared, sir. Fresh start."}
    
    def _search_notes(self, query):
        notes = self._load_notes()
        matches = [n for n in notes if query.lower() in n['content'].lower()]
        if not matches:
            return {'success': True, 'response': f"No notes matching '{query}', sir."}
        
        response = f"🔍 **Notes matching '{query}':**\n\n"
        for n in matches:
            response += f"**#{n['id']}** ({n['created']}): {n['content']}\n"
        
        return {'success': True, 'response': response}
