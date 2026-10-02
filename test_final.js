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
    se.keystroke("f", {using: "command down"});
    delay(1.0);
    se.keystroke("subham");
    delay(2.0);
    se.keyCode(125); // Down Arrow
    delay(0.5);
    se.keyCode(36); // Enter (Focus)
    delay(0.5);
    se.keyCode(36); // Enter (Open)
    delay(1.5);
}
