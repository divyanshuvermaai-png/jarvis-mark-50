function run() {
    var se = Application("System Events");
    var processes = se.processes.whose({name: {"_contains": "WhatsApp"}});
    var wa = null;
    for (var i = 0; i < processes.length; i++) {
        if (processes[i].name().indexOf("AutoFill") === -1) { wa = processes[i]; break; }
    }
    if (wa) {
        wa.frontmost = true;
        delay(1.0);
        se.keystroke("n", {using: "command down"});
        delay(1.0);
        se.keystroke("subham");
        delay(1.5);
        se.keyCode(36); // Enter
        delay(1.5);
    }
}
