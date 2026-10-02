#!/usr/bin/env python3
"""
Interactive macOS Native Touch ID Verification Test for J.A.R.V.I.S.
Prompts the hardware Touch ID sensor on your MacBook Air M5.
"""
import sys
import os

# Add anti2 to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security.biometrics import biometric_authenticator
from tools.builtins.biometrics_tool import BiometricTool

def main():
    print("=" * 60)
    print(" J.A.R.V.I.S.  •  NATIVE macOS TOUCH ID HARDWARE TEST")
    print("=" * 60)

    # 1. Hardware Status Check
    tool = BiometricTool()
    status_res = tool.execute({"action": "status"})
    print("\n🔍 Checking Hardware Sensors...")
    print(status_res.data)

    if not biometric_authenticator.is_touch_id_supported():
        print("\n⚠️  Touch ID is not enrolled or unavailable on this system.")
        return

    print("\n" + "-" * 60)
    print("👉 Touch ID prompt will appear on your screen now.")
    print("👉 Place your enrolled finger on the Touch ID power button.")
    print("-" * 60 + "\n")

    # 2. Trigger hardware Touch ID prompt
    success, error = biometric_authenticator.authenticate(
        reason="Authorize J.A.R.V.I.S. High-Privilege Elevation",
        timeout_sec=25.0
    )

    if success:
        print("\n" + "=" * 60)
        print(" ✅ SUCCESS: TOUCH ID BIOMETRIC AUTHENTICATION VERIFIED!")
        print(" Owner Identity Confirmed: Divyanshu Verma")
        print(" High-privilege clearance granted by Central Security Kernel.")
        print("=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print(f" ❌ FAILED / CANCELLED: {error}")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
