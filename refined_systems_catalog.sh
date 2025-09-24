#!/bin/bash

# Refined Systems Catalog - Focus on FUNCTIONAL CODE only
# Filters out configuration files and binary data

BASE_DIR="/Users/jonathanhollander/AI Code/Notion Template"
OUTPUT_FILE="REFINED_SYSTEMS_CATALOG.md"

echo "# Refined Functional Systems Catalog" > "$OUTPUT_FILE"
echo "Date: $(date)" >> "$OUTPUT_FILE"
echo "Focus: FUNCTIONAL CODE SYSTEMS ONLY" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Function to catalog functional code systems only
catalog_functional_system() {
    local file="$1"
    local system_type="$2"
    local description="$3"

    # Skip if file doesn't exist
    if [[ ! -f "$file" ]]; then
        return
    fi

    # Skip actual binary files but allow all text formats (including RTF, Python scripts, etc.)
    if file "$file" | grep -q -i "jpeg\|png\|gif\|zip\|archive\|data\|ELF\|object file"; then
        return
    fi

    # Allow specifically: text files, RTF files, Python scripts, even if marked as "executable"
    if file "$file" | grep -q -i "text\|RTF\|Python script"; then
        # This is a text-based file we want to process
        :
    elif ! head -1 "$file" >/dev/null 2>&1; then
        # Not readable text
        return
    fi

    # Only process files with significant code content
    lines=$(wc -l < "$file" 2>/dev/null)
    if [[ "$lines" -lt 50 ]]; then
        return
    fi

    # Check for actual code content (classes, functions, significant logic)
    code_indicators=$(grep -c "^class\|^def\|^async def\|^function\|class.*:\|def.*(" "$file" 2>/dev/null)
    if [[ "$code_indicators" -lt 3 ]]; then
        return
    fi

    echo "## $system_type" >> "$OUTPUT_FILE"
    echo "**FILE:** $file" >> "$OUTPUT_FILE"
    echo "**DESCRIPTION:** $description" >> "$OUTPUT_FILE"
    echo "**LINES:** $lines lines" >> "$OUTPUT_FILE"
    echo "**CODE COMPLEXITY:** $code_indicators functions/classes" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    # Show actual code structure
    echo "**FUNCTIONAL COMPONENTS:**" >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"
    grep -n "^class\|^def\|^async def" "$file" 2>/dev/null | head -20 >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    # Show meaningful code sample (not config data)
    echo "**CODE SAMPLE:**" >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"
    # Look for substantial function definitions or class methods
    awk '/^(class|def|async def).*:/{p=1; print} p && /^[[:space:]]+/{print} p && /^[^[:space:]]/ && !/^(class|def|async def)/{p=0}' "$file" | head -25 >> "$OUTPUT_FILE"
    echo '```' >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

echo "=== SCANNING FOR FUNCTIONAL SYSTEMS ==="

# 1. KNOWN CRITICAL SYSTEMS (already verified as functional)
echo "# 🔲 CRITICAL DASHBOARD SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

catalog_functional_system "$BASE_DIR/unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/progress_dashboard.py" \
    "PROGRESS DASHBOARD MANAGER (608 LINES)" \
    "Advanced progress tracking with visual indicators, milestone tracking, ASCII charts"

catalog_functional_system "$BASE_DIR/unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/synced_rollups.py" \
    "SYNCED ROLLUP MANAGER (587 LINES)" \
    "Cross-database synchronization with real-time aggregation and formula management"

catalog_functional_system "$BASE_DIR/Notion_Template_v4.0_Production/asset_generation/review_dashboard.py" \
    "ASSET REVIEW DASHBOARD (v4.0)" \
    "Web-based asset generation dashboard with WebSocket real-time updates"

# 2. SCAN FOR ADDITIONAL FUNCTIONAL SYSTEMS
echo "# 🧠 FUNCTIONAL PYTHON SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Find substantial Python files with real functionality
find "$BASE_DIR" -name "*.py" -type f -size +5000c | while read file; do
    # Skip already cataloged files
    if grep -q "$file" "$OUTPUT_FILE" 2>/dev/null; then
        continue
    fi

    # Check for actual system functionality
    basename_file=$(basename "$file")

    # Look for manager/controller/system patterns
    if grep -q -i -E "class.*Manager|class.*Controller|class.*System|class.*Generator|class.*Handler" "$file"; then
        catalog_functional_system "$file" "FUNCTIONAL SYSTEM: $basename_file" "Python system with manager/controller/generator classes"
    fi
done

# 3. LETTER TEMPLATE SYSTEMS (YAML but with substantial content)
echo "# 📝 SUBSTANTIAL CONTENT SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Only include YAML files with substantial template content
find "$BASE_DIR" -name "*.yaml" -o -name "*.yml" | while read file; do
    # Check for letter template patterns with substantial content
    if grep -q -E "Body:|Template:|Prompt:" "$file" 2>/dev/null; then
        template_count=$(grep -c -E "Body:|Template:|Prompt:" "$file" 2>/dev/null)
        if [[ "$template_count" -gt 5 ]]; then
            lines=$(wc -l < "$file" 2>/dev/null)
            basename_file=$(basename "$file")
            echo "## TEMPLATE SYSTEM: $basename_file" >> "$OUTPUT_FILE"
            echo "**FILE:** $file" >> "$OUTPUT_FILE"
            echo "**DESCRIPTION:** Letter template system with $template_count templates" >> "$OUTPUT_FILE"
            echo "**LINES:** $lines lines" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"

            echo "**TEMPLATE SAMPLES:**" >> "$OUTPUT_FILE"
            echo '```' >> "$OUTPUT_FILE"
            grep -A 3 -B 1 "Title:\|Body:" "$file" 2>/dev/null | head -15 >> "$OUTPUT_FILE"
            echo '```' >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
            echo "---" >> "$OUTPUT_FILE"
            echo "" >> "$OUTPUT_FILE"
        fi
    fi
done

# 4. SUMMARY
echo "# 📊 REFINED CATALOG SUMMARY" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

functional_systems=$(grep -c "^## " "$OUTPUT_FILE")
echo "## Functional Systems Found: $functional_systems" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "**Quality Filters Applied:**" >> "$OUTPUT_FILE"
echo "- Minimum 50 lines of code" >> "$OUTPUT_FILE"
echo "- Minimum 3 functions/classes" >> "$OUTPUT_FILE"
echo "- Excluded binary files" >> "$OUTPUT_FILE"
echo "- Excluded simple configuration files" >> "$OUTPUT_FILE"
echo "- Focused on actual system implementations" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "- **Refined Catalog Completed:** $(date)" >> "$OUTPUT_FILE"

echo "=== REFINED CATALOG COMPLETE ==="
echo "Results saved to: $OUTPUT_FILE"
echo "Found $functional_systems functional systems"