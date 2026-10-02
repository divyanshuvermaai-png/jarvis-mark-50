function run() {
    var se = Application("System Events");
    var wa = se.processes.whose({name: {"_contains": "WhatsApp"}})[0];
    wa.frontmost = true;
    delay(1.0);
    
    // Press Escape a few times to close any existing modals or searches
    se.keyCode(53); delay(0.2); se.keyCode(53); delay(0.5);
    
    se.keystroke("n", {using: "command down"});
    delay(2.0);
    se.keystroke("subham");
    delay(3.0); // Wait long enough for results to load and auto-highlight
    
    se.keyCode(36); // Enter
    delay(1.0);
    se.keyCode(36); // Enter again
    delay(1.5);
}
