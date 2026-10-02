function run() {
    var se = Application("System Events");
    var wa = se.processes.whose({name: {"_contains": "WhatsApp"}})[0];
    wa.frontmost = true;
    delay(1.0);
    se.keystroke("f", {using: "command down"});
    delay(1.0);
    se.keystroke("subham");
    delay(2.0);
    
    // Try Down Arrow with Command
    se.keyCode(125, {using: "command down"}); // Cmd + Down Arrow
    delay(0.5);
    se.keyCode(36); // Enter
    delay(1.5);
}
