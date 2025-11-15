#!/bin/bash
# Clean up development artifacts from capa-server and badsign

set -e

echo "==================================="
echo "capa-server Repository Cleanup"
echo "==================================="
echo ""

cd "$(dirname "$0")"

# Remove development test files
echo "Removing development files..."
rm -f test-api.sh
rm -f INSTALL_SUMMARY.txt
echo " Removed test scripts"

# Clean Python cache in app/
echo "Cleaning Python cache..."
find app/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find app/ -type f -name "*.pyc" -delete 2>/dev/null || true
find app/ -type f -name "*.pyo" -delete 2>/dev/null || true
echo " Removed Python cache from app/"

# Clean any .DS_Store or system files
find . -name ".DS_Store" -delete 2>/dev/null || true
echo " Removed system files"

echo ""
echo "capa-server cleaned "

# Clean badsign if it exists
if [ -d "../badsign" ]; then
    echo ""
    echo "==================================="
    echo "badsign Repository Cleanup"
    echo "==================================="
    echo ""

    cd ../badsign

    echo "Cleaning Python cache..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    echo " Removed Python cache"

    echo "Cleaning build artifacts..."
    rm -rf .pytest_cache/ 2>/dev/null || true
    rm -rf badsign.egg-info/ 2>/dev/null || true
    rm -rf data/ 2>/dev/null || true
    rm -rf dist/ build/ 2>/dev/null || true
    echo " Removed build artifacts"

    # Clean system files
    find . -name ".DS_Store" -delete 2>/dev/null || true
    echo " Removed system files"

    echo ""
    echo "badsign cleaned "
fi

echo ""
echo "==================================="
echo "Cleanup Complete!"
echo "==================================="
echo ""
echo "Removed:"
echo "  • Development test scripts"
echo "  • Python cache (__pycache__, *.pyc)"
echo "  • Build artifacts (.egg-info, .pytest_cache)"
echo "  • System files (.DS_Store)"
echo ""
echo "Preserved:"
echo "  • All documentation (*.md)"
echo "  • Source code"
echo "  • Configuration files"
echo "  • Runtime data (data/)"
echo ""
