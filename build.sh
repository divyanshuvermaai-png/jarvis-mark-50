#!/bin/bash

echo "🚀 Compiling Python Backend..."
# We use pyinstaller to create a directory bundle (fixes 140s startup delay)
pip3 install pyinstaller
python3 -m PyInstaller -y --name jarvis_backend --noconsole main.py

echo "📦 Preparing resources..."
# Move the binary folder to a folder that electron-builder will copy
rm -rf dist/jarvis_core
cp -r dist/jarvis_backend dist/jarvis_core

# Copy the frontend files into the backend's directory so Flask can always find them
cp index.html style.css script.js dist/jarvis_core/

echo "🛠 Building Electron Desktop App..."
# Build the .dmg and .app bundle for macOS
npm run dist

echo "✅ Build Complete! You can find the installable JARVIS.dmg inside the 'dist' folder."
