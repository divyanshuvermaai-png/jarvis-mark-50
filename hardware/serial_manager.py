"""
Arduino/IoT Serial Manager
Auto-detects and manages serial connections to Arduino boards.
"""
import subprocess
import os
import json
import time
import threading


class SerialManager:
    """Manages serial port connections to Arduino and IoT devices."""
    
    CONFIG_FILE = os.path.expanduser('~/.jarvis_system/hardware.json')
    
    def __init__(self):
        self.connection = None
        self.port = None
        self.baudrate = 9600
        self.connected = False
        self._serial = None
        self._read_thread = None
        self._running = False
        self._last_data = ""
        self._load_config()
    
    def _load_config(self):
        """Load saved hardware config."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.port = config.get('port')
                    self.baudrate = config.get('baudrate', 9600)
            except:
                pass
    
    def _save_config(self):
        """Save hardware config."""
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump({'port': self.port, 'baudrate': self.baudrate}, f)
    
    @staticmethod
    def list_ports():
        """List available serial ports on macOS."""
        ports = []
        try:
            # List USB serial devices
            result = subprocess.run(['ls', '/dev/cu.usb*'], capture_output=True, text=True)
            if result.returncode == 0:
                ports.extend(result.stdout.strip().split('\n'))
            
            # Also check for Bluetooth serial
            result = subprocess.run(['ls', '/dev/cu.Bluetooth*'], capture_output=True, text=True)
            if result.returncode == 0:
                ports.extend(result.stdout.strip().split('\n'))
                
        except:
            pass
        
        # Filter empty strings
        ports = [p for p in ports if p.strip()]
        
        return {
            'success': True,
            'ports': ports,
            'data': f"Found {len(ports)} serial port(s): {', '.join(ports)}" if ports else "No serial devices found."
        }
    
    def connect(self, port=None, baudrate=None):
        """Connect to a serial port."""
        if port:
            self.port = port
        if baudrate:
            self.baudrate = baudrate
        
        if not self.port:
            # Try auto-detect
            detected = self.list_ports()
            if detected['ports']:
                self.port = detected['ports'][0]
            else:
                return {'success': False, 'data': 'No serial devices detected. Please connect an Arduino.'}
        
        try:
            import serial
            self._serial = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino reset
            self.connected = True
            self._save_config()
            
            # Start background read thread
            self._running = True
            self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()
            
            return {'success': True, 'data': f'Connected to {self.port} at {self.baudrate} baud'}
        except ImportError:
            return {
                'success': False, 
                'data': 'pyserial not installed. Install with: pip install pyserial'
            }
        except Exception as e:
            return {'success': False, 'data': f'Connection failed: {str(e)}'}
    
    def disconnect(self):
        """Disconnect from serial port."""
        self._running = False
        if self._serial and self._serial.is_open:
            self._serial.close()
        self.connected = False
        return {'success': True, 'data': 'Disconnected from serial device'}
    
    def send(self, data):
        """Send data to the connected device."""
        if not self.connected or not self._serial:
            return {'success': False, 'data': 'Not connected to any device'}
        
        try:
            if not data.endswith('\n'):
                data += '\n'
            self._serial.write(data.encode('utf-8'))
            return {'success': True, 'data': f'Sent: {data.strip()}'}
        except Exception as e:
            return {'success': False, 'data': f'Send failed: {str(e)}'}
    
    def read_last(self):
        """Get the last received data."""
        return {'success': True, 'data': self._last_data or 'No data received yet'}
    
    def _read_loop(self):
        """Background thread to read serial data."""
        while self._running and self._serial and self._serial.is_open:
            try:
                if self._serial.in_waiting:
                    line = self._serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self._last_data = line
                        print(f"  [Arduino] {line}")
                time.sleep(0.1)
            except:
                break
    
    def get_status(self):
        """Get connection status."""
        return {
            'success': True,
            'connected': self.connected,
            'port': self.port,
            'baudrate': self.baudrate,
            'last_data': self._last_data
        }
