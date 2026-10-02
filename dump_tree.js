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
    var UI = wa.windows[0].entireContents();
    var elements = [];
    for (var i = 0; i < UI.length; i++) {
        var el = UI[i];
        if (el.class() === "staticText") {
            elements.push(el.name());
        }
    }
    return JSON.stringify(elements);
}
