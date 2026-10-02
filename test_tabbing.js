function run() {
    var se = Application("System Events");
    var wa = se.processes.whose({name: {"_contains": "WhatsApp"}})[0];
    wa.frontmost = true;
    delay(1.0);
    
    // Clear everything
    se.keyCode(53); delay(0.2); se.keyCode(53); delay(0.2);
    
    se.keystroke("f", {using: "command down"});
    delay(1.0);
    se.keystroke("subham");
    delay(2.0); // Wait for results
    
    // Tab 3 times slowly
    se.keyCode(48); delay(1.0);
    se.keyCode(48); delay(1.0);
    se.keyCode(48); delay(1.0);
    
}
