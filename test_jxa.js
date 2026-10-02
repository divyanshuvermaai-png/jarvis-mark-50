function run() {
    var se = Application("System Events");
    var processes = se.processes.whose({name: {"_contains": "WhatsApp"}});
    if (processes.length === 0) return JSON.stringify({error: "WhatsApp not running"});
    
    var wa = processes[0];
    var win = wa.windows[0];
    
    function dumpElement(el, depth) {
        if (depth > 4) return { role: el.role() }; // limit depth for speed
        try {
            var role = el.role();
            var desc = el.description() || null;
            var name = el.name() || null;
            var title = el.title() || null;
            
            var children = [];
            var uiElements = el.uiElements();
            for (var i = 0; i < uiElements.length; i++) {
                children.push(dumpElement(uiElements[i], depth + 1));
            }
            
            return {
                role: role,
                name: name,
                description: desc,
                title: title,
                children: children.length > 0 ? children : undefined
            };
        } catch (e) {
            return { error: e.toString() };
        }
    }
    
    return JSON.stringify(dumpElement(win, 0));
}
