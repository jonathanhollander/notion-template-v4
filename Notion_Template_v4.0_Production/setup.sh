#!/bin/bash

# Estate Planning Concierge v4.0 - Setup Script
# Helps configure environment and validate deployment

echo "=================================================="
echo "Estate Planning Concierge v4.0 - Setup Assistant"
echo "=================================================="
echo ""

# Check Python version
python_cmd=""
if command -v python3 &> /dev/null; then
    python_cmd="python3"
elif command -v python &> /dev/null; then
    python_cmd="python"
else
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Using Python: $($python_cmd --version)"
echo ""

# Check for required packages
echo "📦 Checking dependencies..."
$python_cmd -c "import requests" 2>/dev/null || {
    echo "Installing requests..."
    $python_cmd -m pip install requests
}
$python_cmd -c "import yaml" 2>/dev/null || {
    echo "Installing PyYAML..."
    $python_cmd -m pip install PyYAML
}
echo "✅ Dependencies installed"
echo ""

# Check for environment variables
echo "🔑 Checking environment variables..."
if [ -z "$NOTION_TOKEN" ]; then
    echo ""
    echo "⚠️  NOTION_TOKEN not set"
    echo ""
    echo "To set your Notion token, run:"
    echo "  export NOTION_TOKEN='your_token_here'"
    echo ""
    echo "Token should start with 'secret_' or 'ntn_'"
    echo "Get your token from: https://www.notion.so/my-integrations"
    echo ""
    read -p "Enter your Notion token (or press Enter to skip): " token
    if [ ! -z "$token" ]; then
        export NOTION_TOKEN="$token"
        echo "✅ NOTION_TOKEN set for this session"
    fi
else
    echo "✅ NOTION_TOKEN is set"
fi

if [ -z "$NOTION_PARENT_PAGEID" ]; then
    echo ""
    echo "⚠️  NOTION_PARENT_PAGEID not set"
    echo ""
    echo "To set your parent page ID, run:"
    echo "  export NOTION_PARENT_PAGEID='your_page_id_here'"
    echo ""
    echo "This is the page where the template will be deployed"
    echo ""
    read -p "Enter your parent page ID (or press Enter to skip): " pageid
    if [ ! -z "$pageid" ]; then
        export NOTION_PARENT_PAGEID="$pageid"
        echo "✅ NOTION_PARENT_PAGEID set for this session"
    fi
else
    echo "✅ NOTION_PARENT_PAGEID is set"
fi

echo ""
echo "=================================================="
echo "Available Commands:"
echo "=================================================="
echo ""
echo "1. Validate deployment configuration:"
echo "   $python_cmd validate_deployment.py"
echo ""
echo "2. Run validation-only check:"
echo "   $python_cmd deploy.py --validate-only --verbose"
echo ""
echo "3. Run dry-run test (simulates deployment):"
echo "   $python_cmd deploy.py --dry-run --verbose"
echo ""
echo "4. Execute full deployment:"
echo "   $python_cmd deploy.py --verbose"
echo ""
echo "5. View help:"
echo "   $python_cmd deploy.py --help"
echo ""

# Ask if user wants to run validation
echo "=================================================="
read -p "Would you like to run validation now? (y/n): " run_validation

if [ "$run_validation" = "y" ] || [ "$run_validation" = "Y" ]; then
    echo ""
    echo "Running validation..."
    echo ""
    $python_cmd validate_deployment.py
fi

echo ""
echo "Setup complete! Use the commands above to proceed."