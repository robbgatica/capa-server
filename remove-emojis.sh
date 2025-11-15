#!/bin/bash
# Remove all emojis from documentation, code, and scripts

set -e

echo "Removing emojis from capa-server..."

# List of files to process (exclude minified Vue.js assets)
FILES=$(find . -type f \( -name "*.md" -o -name "*.py" -o -name "*.sh" -o -name "capa-server-bridge.js" \) -not -path "./static/explorer/assets/*")

# Common emojis to remove
EMOJIS=(
    "📥" "🔍" "🛡️" "📚" "🔧" "💻" "🚀" "✓" "⭐"
    "✅" "❌" "🎯" "📊" "🔐" "🆘" "🐳" "📖" "🤔"
    "⚠️" "🔄" "📝" "🔎" "💡" "🎉" "🎨" "🏗️" "⚙️"
    "🔗" "📄" "🌐" "🖥️" "📦" "🔑" "🗂️" "📋" "🔒"
    "⏳" "📤" "🆕"
)

# Process each file
for file in $FILES; do
    # Skip this script itself
    if [ "$file" = "./remove-emojis.sh" ]; then
        continue
    fi

    # Create sed command to remove all emojis
    sed_cmd="sed -i"
    for emoji in "${EMOJIS[@]}"; do
        sed_cmd="$sed_cmd -e 's/$emoji//g'"
    done
    sed_cmd="$sed_cmd '$file'"

    # Execute sed
    for emoji in "${EMOJIS[@]}"; do
        sed -i "s/$emoji//g" "$file"
    done

    # Also remove common emoji patterns with spaces
    sed -i 's/\s*<span>[^<]*<\/span>\s*//g' "$file" 2>/dev/null || true
done

echo "Emojis removed from capa-server"
