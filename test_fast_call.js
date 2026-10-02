function run() {
    var se = Application("System Events");
    var wa = Application("WhatsApp");
    
    wa.activate();
    delay(0.1);
    
    // Clear search
    se.keystroke("f", {using: ["command down", "option down"]}); // sometimes cmd+opt+f is search
    // Actually Cmd+F is search
    se.keystroke("f", {using: "command down"});
    delay(0.1);
    se.keyCode(51, {using: "command down"}); // clear
    delay(0.1);
    
    se.keystroke("Subham 702");
    
    // Wait for UI to update. Instead of hardcoded delay, maybe poll?
    // JXA UI polling is slow, let's just use a short delay
    delay(0.5);
    
    se.keyCode(125); delay(0.05); // Down
    se.keyCode(125); delay(0.05); // Down
    se.keyCode(36); // Enter
    delay(0.2);
    
    // Trigger call
    var chatMenu = wa.menuBars[0].menuBarItems[4];
    var items = chatMenu.menus[0].menuItems;
    var found = false;
    for (var i=0; i<items.length; i++) {
        var name = items[i].name();
        if (name && name.indexOf("Voice Call") !== -1) {
            items[i].click();
            found = true;
            break;
        }
    }
    return found;
}
