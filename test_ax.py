import sys
import Quartz
import ApplicationServices
from AppKit import NSWorkspace

def get_whatsapp_pid():
    workspace = NSWorkspace.sharedWorkspace()
    for app in workspace.runningApplications():
        name = app.localizedName() or ""
        if "WhatsApp" in name and "AutoFill" not in name:
            return app.processIdentifier()
    return None

pid = get_whatsapp_pid()
if not pid:
    print("WhatsApp is not running.")
    sys.exit(1)

print(f"WhatsApp PID: {pid}")

app_element = ApplicationServices.AXUIElementCreateApplication(pid)
print(f"App Element: {app_element}")

err, children = ApplicationServices.AXUIElementCopyAttributeValue(app_element, "AXChildren", None)
if err == ApplicationServices.kAXErrorSuccess:
    print(f"Found {len(children)} children (windows/menus)")
    for child in children:
        err, role = ApplicationServices.AXUIElementCopyAttributeValue(child, "AXRole", None)
        print(f"Child role: {role}")
else:
    print(f"Could not get children, error code: {err}")
