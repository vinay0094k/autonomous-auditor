#!/bin/bash
# Autonomous Auditor - Easy Installation Script
# Run this once to install the auditor system-wide

set -e

INSTALL_DIR="/usr/local/bin"
AUDITOR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Installing Autonomous Auditor..."

# Check if running as root for system-wide install
if [[ $EUID -eq 0 ]]; then
    echo "Installing system-wide to $INSTALL_DIR"
    
    # Create symlinks in /usr/local/bin
    ln -sf "$AUDITOR_DIR/autonomous-auditor" "$INSTALL_DIR/autonomous-auditor"
    ln -sf "$AUDITOR_DIR/audit-policy" "$INSTALL_DIR/audit-policy"
    
    echo "✅ Installed system-wide commands:"
    echo "   - autonomous-auditor (main CLI)"
    echo "   - audit-policy (policy enforcement)"
    
else
    # User installation - add to ~/.local/bin
    LOCAL_BIN="$HOME/.local/bin"
    mkdir -p "$LOCAL_BIN"
    
    ln -sf "$AUDITOR_DIR/autonomous-auditor" "$LOCAL_BIN/autonomous-auditor"
    ln -sf "$AUDITOR_DIR/audit-policy" "$LOCAL_BIN/audit-policy"
    
    echo "✅ Installed user commands to $LOCAL_BIN:"
    echo "   - autonomous-auditor (main CLI)"
    echo "   - audit-policy (policy enforcement)"
    
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
        echo ""
        echo "⚠️  Add $LOCAL_BIN to your PATH:"
        echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
        echo "   source ~/.bashrc"
    fi
fi

# Install Python dependencies
echo ""
echo "📦 Setting up Python environment..."
cd "$AUDITOR_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies in virtual environment..."
source .venv/bin/activate

if command -v uv &> /dev/null; then
    echo "Using uv for dependency management..."
    uv sync 2>/dev/null || uv add langgraph ollama rich python-dotenv pyyaml
else
    echo "Using pip for dependency management..."
    pip install -r requirements.txt 2>/dev/null || pip install langgraph ollama rich python-dotenv pyyaml
fi

deactivate

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Usage from any directory:"
echo "  autonomous-auditor --mode repo_hygiene \"Audit this repo\" --format json --out audit.json"
echo "  audit-policy audit.json --pack soc2"
echo ""
echo "Test installation:"
echo "  autonomous-auditor --help"
