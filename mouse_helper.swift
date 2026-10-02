import Foundation
import CoreGraphics

setbuf(stdout, nil)
setbuf(stdin, nil)

let mainDisplay = CGMainDisplayID()
let screenW = Double(CGDisplayPixelsWide(mainDisplay))
let screenH = Double(CGDisplayPixelsHigh(mainDisplay))
let source = CGEventSource(stateID: .combinedSessionState)

func postEvent(_ ev: CGEvent?) {
    guard let ev = ev else { return }
    ev.post(tap: .cghidEventTap)
    ev.post(tap: .cgSessionEventTap)
}

print("READY \(Int(screenW)) \(Int(screenH))")

while let line = readLine() {
    let parts = line.split(separator: " ")
    guard !parts.isEmpty else { continue }
    let cmd = parts[0]
    
    switch cmd {
    case "M":
        if parts.count >= 3, let x = Double(parts[1]), let y = Double(parts[2]) {
            let pt = CGPoint(x: x, y: y)
            CGDisplayMoveCursorToPoint(mainDisplay, pt)
            let ev = CGEvent(mouseEventSource: source, mouseType: .mouseMoved, mouseCursorPosition: pt, mouseButton: .left)
            postEvent(ev)
        }
    case "C":
        let loc: CGPoint
        if parts.count >= 3, let x = Double(parts[1]), let y = Double(parts[2]) {
            loc = CGPoint(x: x, y: y)
            CGDisplayMoveCursorToPoint(mainDisplay, loc)
        } else {
            loc = CGEvent(source: nil)?.location ?? .zero
        }
        let down = CGEvent(mouseEventSource: source, mouseType: .leftMouseDown, mouseCursorPosition: loc, mouseButton: .left)
        down?.setIntegerValueField(.mouseEventClickState, value: 1)
        postEvent(down)
        usleep(35000)
        let up = CGEvent(mouseEventSource: source, mouseType: .leftMouseUp, mouseCursorPosition: loc, mouseButton: .left)
        up?.setIntegerValueField(.mouseEventClickState, value: 1)
        postEvent(up)
    case "RC":
        let loc: CGPoint
        if parts.count >= 3, let x = Double(parts[1]), let y = Double(parts[2]) {
            loc = CGPoint(x: x, y: y)
            CGDisplayMoveCursorToPoint(mainDisplay, loc)
        } else {
            loc = CGEvent(source: nil)?.location ?? .zero
        }
        let down = CGEvent(mouseEventSource: source, mouseType: .rightMouseDown, mouseCursorPosition: loc, mouseButton: .right)
        down?.setIntegerValueField(.mouseEventClickState, value: 1)
        postEvent(down)
        usleep(35000)
        let up = CGEvent(mouseEventSource: source, mouseType: .rightMouseUp, mouseCursorPosition: loc, mouseButton: .right)
        up?.setIntegerValueField(.mouseEventClickState, value: 1)
        postEvent(up)
    case "DC":
        let loc: CGPoint
        if parts.count >= 3, let x = Double(parts[1]), let y = Double(parts[2]) {
            loc = CGPoint(x: x, y: y)
            CGDisplayMoveCursorToPoint(mainDisplay, loc)
        } else {
            loc = CGEvent(source: nil)?.location ?? .zero
        }
        let down1 = CGEvent(mouseEventSource: source, mouseType: .leftMouseDown, mouseCursorPosition: loc, mouseButton: .left)
        down1?.setIntegerValueField(.mouseEventClickState, value: 1)
        postEvent(down1)
        usleep(25000)
        let up1 = CGEvent(mouseEventSource: source, mouseType: .leftMouseUp, mouseCursorPosition: loc, mouseButton: .left)
        up1?.setIntegerValueField(.mouseEventClickState, value: 1)
        postEvent(up1)
        usleep(45000)
        let down2 = CGEvent(mouseEventSource: source, mouseType: .leftMouseDown, mouseCursorPosition: loc, mouseButton: .left)
        down2?.setIntegerValueField(.mouseEventClickState, value: 2)
        postEvent(down2)
        usleep(25000)
        let up2 = CGEvent(mouseEventSource: source, mouseType: .leftMouseUp, mouseCursorPosition: loc, mouseButton: .left)
        up2?.setIntegerValueField(.mouseEventClickState, value: 2)
        postEvent(up2)
    case "D":
        let loc: CGPoint
        if parts.count >= 3, let x = Double(parts[1]), let y = Double(parts[2]) {
            loc = CGPoint(x: x, y: y)
            CGDisplayMoveCursorToPoint(mainDisplay, loc)
        } else {
            loc = CGEvent(source: nil)?.location ?? .zero
        }
        let down = CGEvent(mouseEventSource: source, mouseType: .leftMouseDown, mouseCursorPosition: loc, mouseButton: .left)
        down?.setIntegerValueField(.mouseEventClickState, value: 1)
        postEvent(down)
    case "DR":
        if parts.count >= 3, let x = Double(parts[1]), let y = Double(parts[2]) {
            let pt = CGPoint(x: x, y: y)
            CGDisplayMoveCursorToPoint(mainDisplay, pt)
            let drag = CGEvent(mouseEventSource: source, mouseType: .leftMouseDragged, mouseCursorPosition: pt, mouseButton: .left)
            postEvent(drag)
        }
    case "U":
        let loc: CGPoint
        if parts.count >= 3, let x = Double(parts[1]), let y = Double(parts[2]) {
            loc = CGPoint(x: x, y: y)
            CGDisplayMoveCursorToPoint(mainDisplay, loc)
        } else {
            loc = CGEvent(source: nil)?.location ?? .zero
        }
        let up = CGEvent(mouseEventSource: source, mouseType: .leftMouseUp, mouseCursorPosition: loc, mouseButton: .left)
        up?.setIntegerValueField(.mouseEventClickState, value: 1)
        postEvent(up)
    case "S":
        if parts.count >= 2, let dy = Int32(parts[1]) {
            let ev = CGEvent(scrollWheelEvent2Source: source, units: .line, wheelCount: 1, wheel1: dy, wheel2: 0, wheel3: 0)
            postEvent(ev)
        }
    case "Q":
        exit(0)
    default:
        break
    }
}
