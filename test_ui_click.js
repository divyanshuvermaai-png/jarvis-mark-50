function run() {
    var se = Application("System Events");
    var processes = se.processes.whose({name: {"_contains": "WhatsApp"}});
    var wa = processes[0];
    if (processes.length > 1) {
        for (var i = 0; i < processes.length; i++) {
            if (processes[i].name().indexOf("AutoFill") === -1) { wa = processes[i]; break; }
        }
    }
    wa.frontmost = true;
    delay(1.0);
    
    // Type in global search
    se.keystroke("f", {using: "command down"});
    delay(1.0);
    se.keystroke("subham");
    delay(2.0);
    
    // Now use accessibility to find the search result and click it
    var window = wa.windows[0];
    // Find all static texts or UI elements containing the name
    var elements = window.entireContents();
    var target = null;
    for (var i = 0; i < elements.length; i++) {
        var el = elements[i];
        if (el.class() === "staticText" && el.name() && el.name().toLowerCase().indexOf("subham") !== -1) {
            target = el;
            break;
        }
    }
    
    if (target) {
        // Try to select/click it
        // Usually, the static text is inside a row or group that is clickable
        var parent = target.attributeValue("AXParent");
        if (parent && parent.class() === "group") {
            se.click(parent);
        } else {
            se.click(target);
        }
        return JSON.stringify({success: true, found: target.name()});
    }
    return JSON.stringify({success: false, reason: "not found"});
}
