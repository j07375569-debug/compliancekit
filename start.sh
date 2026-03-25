#!/bin/bash
# ComplianceKit — Start Script
# Run this to launch the full application

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║         ComplianceKit v1.0             ║"
echo "  ║   AI-Powered Compliance Autopilot      ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

# Initialize database if needed
python3 server/database.py

# Start the server
echo "Starting server on http://localhost:3000 ..."
echo "Press Ctrl+C to stop."
echo ""
python3 server/app.py
