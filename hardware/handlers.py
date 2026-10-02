"""
Arduino Command Handlers
Maps natural language commands to Arduino serial commands.
"""
from .serial_manager import SerialManager


class ArduinoHandler:
    """High-level Arduino control with natural language command mapping."""
    
    # Default command map: voice command keyword -> serial command to send
    COMMAND_MAP = {
        # LED control
        'turn on the light': 'LED_ON',
        'turn off the light': 'LED_OFF',
        'lights on': 'LED_ON',
        'lights off': 'LED_OFF',
        'blink': 'LED_BLINK',
        
        # Relay control
        'turn on relay': 'RELAY_ON',
        'turn off relay': 'RELAY_OFF',
        'switch on': 'RELAY_ON',
        'switch off': 'RELAY_OFF',
        
        # Servo control
        'open door': 'SERVO_OPEN',
        'close door': 'SERVO_CLOSE',
        'lock door': 'SERVO_LOCK',
        'unlock door': 'SERVO_UNLOCK',
        
        # Sensor reading
        'read temperature': 'READ_TEMP',
        'read humidity': 'READ_HUMIDITY',
        'read sensor': 'READ_ALL',
        'sensor data': 'READ_ALL',
        
        # Motor control
        'motor on': 'MOTOR_ON',
        'motor off': 'MOTOR_OFF',
        'fan on': 'MOTOR_ON',
        'fan off': 'MOTOR_OFF',
        
        # RGB LED
        'red light': 'RGB_RED',
        'green light': 'RGB_GREEN',
        'blue light': 'RGB_BLUE',
        'white light': 'RGB_WHITE',
        'rainbow': 'RGB_RAINBOW',
        
        # Buzzer
        'beep': 'BUZZER_BEEP',
        'alarm on': 'BUZZER_ON',
        'alarm off': 'BUZZER_OFF',
    }
    
    def __init__(self):
        self.serial = SerialManager()
    
    def is_connected(self):
        return self.serial.connected
    
    def connect(self, port=None, baudrate=None):
        return self.serial.connect(port, baudrate)
    
    def disconnect(self):
        return self.serial.disconnect()
    
    def handle_command(self, message):
        """
        Try to match a natural language message to an Arduino command.
        Returns: {'success': bool, 'data': str, 'matched': bool}
        """
        msg = message.lower().strip()
        
        # Try exact matches first
        for trigger, command in self.COMMAND_MAP.items():
            if trigger in msg:
                if not self.serial.connected:
                    return {
                        'success': False,
                        'data': 'No Arduino connected. Please connect a device first.',
                        'matched': True
                    }
                result = self.serial.send(command)
                result['matched'] = True
                
                # If it's a sensor read, wait for response
                if command.startswith('READ_'):
                    import time
                    time.sleep(1)
                    sensor_data = self.serial.read_last()
                    result['sensor_data'] = sensor_data.get('data', '')
                
                return result
        
        return {'success': False, 'data': '', 'matched': False}
    
    def send_raw(self, command):
        """Send a raw serial command."""
        return self.serial.send(command)
    
    def get_status(self):
        """Get Arduino connection status."""
        status = self.serial.get_status()
        status['command_count'] = len(self.COMMAND_MAP)
        return status
    
    def list_commands(self):
        """List all available commands."""
        return {
            'success': True,
            'commands': [
                {'trigger': k, 'serial_cmd': v} 
                for k, v in self.COMMAND_MAP.items()
            ]
        }
