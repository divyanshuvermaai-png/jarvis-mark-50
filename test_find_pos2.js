function run() {
    var se = Application("System Events");
    var wa = se.processes.whose({name: {"_contains": "WhatsApp"}})[0];
    wa.frontmost = true;
    delay(1.0);
    se.keystroke("f", {using: "command down"});
    delay(1.0);
    // Clear existing text by selecting all and deleting
    se.keystroke("a", {using: "command down"});
    delay(0.2);
    se.keyCode(51); // Delete
    delay(0.5);
    se.keystroke("subham");
    delay(2.0);
    
    function findElementPos(element, targetName, depth) {
        if (depth > 6) return null;
        try {
            var name = element.name();
            if (name && name.toLowerCase().indexOf(targetName.toLowerCase()) !== -1 && element.class() === "staticText") {
                return element.position();
            }
            var children = element.uiElements();
            for (var i = 0; i < children.length; i++) {
                var pos = findElementPos(children[i], targetName, depth + 1);
                if (pos) return pos;
            }
        } catch(e) {}
        return null;
    }
    
    var pos = findElementPos(wa.windows[0], "subham 702", 0); // Be specific to find the contact row
    return JSON.stringify(pos);
}
