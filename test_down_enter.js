function run() {
    var se = Application("System Events");
    var wa = se.processes.whose({name: {"_contains": "WhatsApp"}})[0];
    wa.frontmost = true;
    delay(1.0);
    
    // Clear everything
    se.keyCode(53); delay(0.2); se.keyCode(53); delay(0.2);
    
    se.keystroke("f", {using: "command down"});
    delay(1.0);
    se.keystroke("a", {using: "command down"});
    delay(0.2);
    se.keyCode(51); // Delete
    delay(0.2);
    
    se.keystroke("subham");
    delay(2.0); // Wait for results
    
    // Highlight the top result
    se.keyCode(125); // Down Arrow
    delay(1.0);
    
    // Press Enter to open
    se.keyCode(36); // Enter
    delay(1.5);
}
