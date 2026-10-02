"""
System Tools Plugin for J.A.R.V.I.S.
Battery status, IP address, Wi-Fi info, uptime, dark mode toggle.
"""
import subprocess
import re
import sys
sys.path.insert(0, '..')
from plugin_system import PluginBase


class SystemToolsPlugin(PluginBase):
    name = "system_tools"
    description = "Battery, IP, Wi-Fi, uptime, dark mode, and more system utilities"
    version = "1.0.0"
    commands = [
        'battery', 'battery level', 'is it charging',
        'my ip', 'ip address', 'what is my ip',
        'wifi', 'wi-fi', 'connected to',
        'uptime', 'how long',
        'dark mode', 'light mode', 'toggle dark',
        'empty trash', 'clear trash',
        'do not disturb', 'dnd', 'focus mode',
        'shutdown', 'restart', 'reboot',
    ]
    
    def execute(self, message, params=None):
        msg = message.lower().strip()
        
        if any(k in msg for k in ['battery', 'charging']):
            return self._battery()
        if any(k in msg for k in ['my ip', 'ip address', 'what is my ip']):
            return self._ip_address()
        if any(k in msg for k in ['wifi', 'wi-fi', 'connected to']):
            return self._wifi_info()
        if any(k in msg for k in ['uptime', 'how long']):
            return self._uptime()
        if 'dark mode' in msg:
            return self._toggle_dark_mode(enable=True)
        if 'light mode' in msg:
            return self._toggle_dark_mode(enable=False)
        if any(k in msg for k in ['empty trash', 'clear trash']):
            return self._empty_trash()
        if any(k in msg for k in ['do not disturb', 'dnd', 'focus mode']):
            return self._toggle_dnd()
        if 'restart' in msg or 'reboot' in msg:
            return {'success': False, 'response': "Sir, restarting the system requires manual confirmation. Use the Apple menu to restart."}
        if 'shutdown' in msg:
            return {'success': False, 'response': "Sir, shutting down requires manual confirmation. Use the Apple menu to shut down."}
        
        return {'success': False, 'response': "I didn't catch the specific system command, sir."}
    
    def _battery(self):
        try:
            result = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True, timeout=5)
            output = result.stdout
            
            # Parse battery percentage
            match = re.search(r'(\d+)%', output)
            percent = match.group(1) if match else '?'
            
            charging = 'charging' in output.lower() or 'ac power' in output.lower()
            status = '⚡ Charging' if charging else '🔋 On Battery'
            
            # Time remaining
            time_match = re.search(r'(\d+:\d+) remaining', output)
            time_left = time_match.group(1) if time_match else 'calculating...'
            
            return {
                'success': True,
                'response': f"**Battery Status**\n\n🔋 **{percent}%** — {status}\n⏱️ Time remaining: {time_left}"
            }
        except Exception as e:
            return {'success': False, 'response': f"Battery check failed: {e}"}
    
    def _ip_address(self):
        try:
            # Local IP
            local_result = subprocess.run(
                ['ipconfig', 'getifaddr', 'en0'],
                capture_output=True, text=True, timeout=5
            )
            local_ip = local_result.stdout.strip() or 'Not connected'
            
            # Public IP
            import urllib.request
            req = urllib.request.Request('https://api.ipify.org', headers={'User-Agent': 'Jarvis/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                public_ip = resp.read().decode('utf-8').strip()
            
            return {
                'success': True,
                'response': f"**Network Identity**\n\n🏠 Local IP: `{local_ip}`\n🌐 Public IP: `{public_ip}`"
            }
        except Exception as e:
            return {'success': False, 'response': f"IP lookup failed: {e}"}
    
    def _wifi_info(self):
        try:
            # macOS 15+ uses wdutil, older uses airport
            result = subprocess.run(
                ['/System/Library/PrivateFrameworks/Apple80211.framework/Resources/airport', '-I'],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout
            
            ssid_match = re.search(r'\s+SSID:\s+(.+)', output)
            bssid_match = re.search(r'\s+BSSID:\s+(.+)', output)
            rssi_match = re.search(r'agrCtlRSSI:\s+(-?\d+)', output)
            channel_match = re.search(r'\s+channel:\s+(.+)', output)
            
            ssid = ssid_match.group(1).strip() if ssid_match else 'Unknown'
            rssi = int(rssi_match.group(1)) if rssi_match else None
            channel = channel_match.group(1).strip() if channel_match else '?'
            
            signal = 'Excellent' if rssi and rssi > -50 else ('Good' if rssi and rssi > -65 else ('Fair' if rssi and rssi > -75 else 'Weak'))
            
            return {
                'success': True,
                'response': f"**Wi-Fi Connection**\n\n📶 Network: **{ssid}**\n📊 Signal: {signal} ({rssi} dBm)\n📡 Channel: {channel}"
            }
        except Exception as e:
            return {'success': False, 'response': f"Wi-Fi info failed: {e}"}
    
    def _uptime(self):
        try:
            result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
            uptime_str = result.stdout.strip()
            
            # Extract the uptime portion
            match = re.search(r'up\s+(.+?),\s+\d+\s+user', uptime_str)
            uptime = match.group(1).strip() if match else uptime_str
            
            return {
                'success': True,
                'response': f"**System Uptime**\n\n⏱️ Your Mac has been running for **{uptime}**"
            }
        except Exception as e:
            return {'success': False, 'response': f"Uptime check failed: {e}"}
    
    def _toggle_dark_mode(self, enable=True):
        mode = 'true' if enable else 'false'
        mode_name = 'Dark' if enable else 'Light'
        script = f'''
        tell application "System Events"
            tell appearance preferences
                set dark mode to {mode}
            end tell
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {
                'success': True,
                'response': f"🎨 Switched to **{mode_name} Mode**, sir."
            }
        except Exception as e:
            return {'success': False, 'response': f"Mode switch failed: {e}"}
    
    def _empty_trash(self):
        script = '''
        tell application "Finder"
            empty the trash
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=10)
            return {
                'success': True,
                'response': "🗑️ Trash emptied, sir. Clean and clear."
            }
        except Exception as e:
            return {'success': False, 'response': f"Trash operation failed: {e}"}
    
    def _toggle_dnd(self):
        # macOS Monterey+ uses Focus mode
        script = '''
        tell application "System Events"
            tell process "ControlCenter"
                click menu bar item "Focus" of menu bar 1
            end tell
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            return {
                'success': True,
                'response': "🔕 Focus mode toggled, sir."
            }
        except:
            return {
                'success': True,
                'response': "Sir, please toggle Do Not Disturb manually from Control Center. macOS restricts programmatic access."
            }
