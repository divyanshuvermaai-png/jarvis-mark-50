"""
J.A.R.V.I.S. Plugin System
Auto-discovers and loads plugins from the plugins/ directory.
Each plugin is a Python file with a standard interface.
"""
import os
import importlib
import importlib.util
import inspect


class PluginBase:
    """Base class for all Jarvis plugins."""
    
    # Plugin metadata — override in subclass
    name = "unnamed_plugin"
    description = "No description"
    version = "1.0.0"
    commands = []  # List of command patterns this plugin handles
    
    def __init__(self, jarvis_context=None):
        """
        Initialize plugin with optional Jarvis context.
        jarvis_context: dict with {'ai_client', 'ai_config', 'config_dir'}
        """
        self.context = jarvis_context or {}
    
    def can_handle(self, message):
        """
        Check if this plugin can handle the given message.
        Returns: bool
        """
        msg_lower = message.lower().strip()
        return any(cmd in msg_lower for cmd in self.commands)
    
    def execute(self, message, params=None):
        """
        Execute the plugin's action.
        Returns: {'success': bool, 'response': str, 'data': any}
        """
        raise NotImplementedError("Plugin must implement execute()")
    
    def get_info(self):
        """Return plugin metadata."""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'commands': self.commands
        }


class PluginLoader:
    """Discovers and manages Jarvis plugins."""
    
    def __init__(self, plugin_dir=None):
        self.plugin_dir = plugin_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'plugins'
        )
        self.plugins = {}  # name -> PluginBase instance
        self._ensure_plugin_dir()
    
    def _ensure_plugin_dir(self):
        """Create plugins directory if it doesn't exist."""
        os.makedirs(self.plugin_dir, exist_ok=True)
        init_file = os.path.join(self.plugin_dir, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("# Jarvis Plugins Directory\n")
    
    def discover_plugins(self, jarvis_context=None):
        """Scan the plugins directory and load all valid plugins."""
        self.plugins = {}
        
        if not os.path.exists(self.plugin_dir):
            return
        
        for filename in os.listdir(self.plugin_dir):
            if filename.startswith('_') or not filename.endswith('.py'):
                continue
            
            filepath = os.path.join(self.plugin_dir, filename)
            module_name = filename[:-3]
            
            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{module_name}", filepath
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find all PluginBase subclasses in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, PluginBase) and obj is not PluginBase:
                        try:
                            instance = obj(jarvis_context)
                            self.plugins[instance.name] = instance
                            print(f"  🔌 Plugin loaded: {instance.name} v{instance.version}")
                        except Exception as e:
                            print(f"  ⚠️  Plugin init failed ({name}): {e}")
                            
            except Exception as e:
                print(f"  ⚠️  Failed to load plugin '{filename}': {e}")
        
        print(f"  ✅ {len(self.plugins)} plugin(s) loaded")
        return self.plugins
    
    def find_handler(self, message):
        """
        Find a plugin that can handle the given message.
        Returns: (plugin_name, plugin_instance) or (None, None)
        """
        for name, plugin in self.plugins.items():
            if plugin.can_handle(message):
                return name, plugin
        return None, None
    
    def execute_plugin(self, plugin_name, message, params=None):
        """Execute a specific plugin by name."""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return {'success': False, 'response': f'Plugin "{plugin_name}" not found.'}
        
        try:
            return plugin.execute(message, params)
        except Exception as e:
            return {'success': False, 'response': f'Plugin error: {str(e)}'}
    
    def list_plugins(self):
        """List all loaded plugins."""
        return [p.get_info() for p in self.plugins.values()]
    
    def reload_plugins(self, jarvis_context=None):
        """Reload all plugins (useful for development)."""
        self.discover_plugins(jarvis_context)
        return self.list_plugins()
