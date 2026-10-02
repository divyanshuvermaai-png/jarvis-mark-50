function run() {
    var se = Application("System Events");
    var wa = se.processes.whose({name: {"_contains": "WhatsApp"}})[0];
    wa.frontmost = true;
    delay(1.0);
    
    // Clear everything first
    se.keyCode(53); delay(0.2); se.keyCode(53); delay(0.2); // Esc
    
    se.keystroke("f", {using: "command down"});
    delay(1.0);
    se.keystroke("a", {using: "command down"});
    delay(0.2);
    se.keyCode(51); // Delete
    delay(0.2);
    
    se.keystroke("subham");
    delay(2.0); // Wait for results
    
    se.keyCode(125); // Down Arrow to highlight
    delay(0.5);
    se.keyCode(49); // Space
    delay(0.5);
    se.keyCode(36); // Enter
    delay(1.5);
}
