#!/bin/bash

# Comprehensive System Cataloging Script
# Catalogs ALL content systems found by comprehensive discovery

BASE_DIR="/Users/jonathanhollander/AI Code/Notion Template"
OUTPUT_FILE="ALL_DISCOVERED_SYSTEMS_CATALOG.md"

echo "# Complete Catalog of ALL Discovered Content Systems" > "$OUTPUT_FILE"
echo "Date: $(date)" >> "$OUTPUT_FILE"
echo "Based on comprehensive content discovery results" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Function to catalog a system with full analysis
catalog_system() {
    local file="$1"
    local system_type="$2"
    local description="$3"

    if [[ -f "$file" ]]; then
        echo "## $system_type" >> "$OUTPUT_FILE"
        echo "**FILE:** $file" >> "$OUTPUT_FILE"
        echo "**DESCRIPTION:** $description" >> "$OUTPUT_FILE"
        echo "**SIZE:** $(wc -c < "$file" 2>/dev/null || echo 'N/A') bytes" >> "$OUTPUT_FILE"
        echo "**LINES:** $(wc -l < "$file" 2>/dev/null || echo 'N/A') lines" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"

        # Extract key classes/functions
        echo "**KEY COMPONENTS:**" >> "$OUTPUT_FILE"
        echo "\`\`\`" >> "$OUTPUT_FILE"
        grep -n "^class\|^def\|^async def" "$file" 2>/dev/null | head -15 >> "$OUTPUT_FILE"
        echo "\`\`\`" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"

        # Show first significant section
        echo "**SYSTEM OVERVIEW:**" >> "$OUTPUT_FILE"
        echo "\`\`\`" >> "$OUTPUT_FILE"
        head -30 "$file" | tail -20 >> "$OUTPUT_FILE"
        echo "\`\`\`" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "---" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
}

echo "=== CATALOGING ALL DISCOVERED SYSTEMS ==="

# 1. DASHBOARD AND VISUALIZATION SYSTEMS
echo "# 🔲 DASHBOARD & VISUALIZATION SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

catalog_system "$BASE_DIR/unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/progress_dashboard.py" \
    "PROGRESS DASHBOARD MANAGER (608 LINES)" \
    "Comprehensive dashboard system with progress bars, milestone tracking, activity timelines, status summaries, metric cards, ASCII chart generation"

catalog_system "$BASE_DIR/Notion_Template_v4.0_Production/asset_generation/review_dashboard.py" \
    "ASSET REVIEW DASHBOARD (CURRENT v4.0)" \
    "Web-based asset generation dashboard with real-time WebSocket updates, approval workflows, cost tracking"

# 2. DATABASE AND TRACKING SYSTEMS
echo "# 🗄️ DATABASE & TRACKING SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

catalog_system "$BASE_DIR/unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/synced_rollups.py" \
    "SYNCED ROLLUP MANAGER (587 LINES)" \
    "Cross-database rollup system with real-time aggregation, automatic formula synchronization, rollup caching, change detection and propagation"

# 3. EMOTIONAL INTELLIGENCE SYSTEMS
echo "# ❤️ EMOTIONAL INTELLIGENCE & EQ SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

catalog_system "$BASE_DIR/Notion_Template_v4.0_Production/asset_generation/emotional_elements.py" \
    "EMOTIONAL INTELLIGENCE MANAGER (32KB SYSTEM)" \
    "Sophisticated contextual emotional design elements, life stage mapping, comfort level adjustments, grief and bereavement support"

catalog_system "$BASE_DIR/Notion_Template_v4.0_Production/asset_generation/emotional_defaults.yaml" \
    "EMOTIONAL DEFAULTS CONFIGURATION" \
    "Default emotional intelligence settings and configurations for various contexts"

# 4. LETTER TEMPLATE SYSTEMS
echo "# 📝 LETTER TEMPLATE SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

catalog_system "$BASE_DIR/unpacked-zips/legacy_concierge_gold_v3_8_2/split_yaml/03_letters.yaml" \
    "COMPLETE 17-LETTER TEMPLATE SYSTEM" \
    "Full letter template system with Body/Disclaimer/Prompt structure, toggle functionality, audience targeting"

# 5. SECURITY AND MONITORING SYSTEMS
echo "# 🔒 SECURITY & MONITORING SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Search for security-related files
find "$BASE_DIR" -name "*security*" -o -name "*audit*" -o -name "*monitor*" | while read file; do
    if [[ -f "$file" ]]; then
        basename_file=$(basename "$file")
        catalog_system "$file" "SECURITY/MONITORING: $basename_file" "Security, audit, or monitoring system component"
    fi
done

# 6. ONBOARDING AND WORKFLOW SYSTEMS
echo "# 🚀 ONBOARDING & WORKFLOW SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Search for onboarding/workflow files
find "$BASE_DIR" -name "*onboard*" -o -name "*workflow*" -o -name "*wizard*" | while read file; do
    if [[ -f "$file" ]]; then
        basename_file=$(basename "$file")
        catalog_system "$file" "ONBOARDING/WORKFLOW: $basename_file" "User onboarding, workflow, or wizard system"
    fi
done

# 7. INTERACTIVE CONTENT SYSTEMS
echo "# 🔄 INTERACTIVE CONTENT SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Search for toggle, accordion, interactive content
find "$BASE_DIR" \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" \) -type f -exec grep -l -i -E "toggle|accordion|expand|collapse|interactive" {} \; | while read file; do
    basename_file=$(basename "$file")

    # Get toggle/interactive content count
    toggle_count=$(grep -c -i -E "toggle|accordion|expand|collapse" "$file" 2>/dev/null)
    if [[ -z "$toggle_count" ]]; then
        toggle_count=0
    fi

    if [[ "$toggle_count" -gt 3 ]]; then
        catalog_system "$file" "INTERACTIVE CONTENT: $basename_file ($toggle_count matches)" "Interactive content with toggles, accordions, expandable sections"
    fi
done

# 8. PROMPT AND GUIDANCE SYSTEMS
echo "# 💬 PROMPT & GUIDANCE SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Search for prompt systems
find "$BASE_DIR" \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" \) -type f -exec grep -l -i -E "prompt|guidance|instruction|help.*text|tooltip" {} \; | while read file; do
    basename_file=$(basename "$file")

    # Get prompt content count
    prompt_count=$(grep -c -i -E "prompt|guidance|instruction" "$file" 2>/dev/null)
    if [[ -z "$prompt_count" ]]; then
        prompt_count=0
    fi

    if [[ "$prompt_count" -gt 5 ]]; then
        catalog_system "$file" "PROMPT/GUIDANCE: $basename_file ($prompt_count matches)" "User guidance, prompts, instructions, help text systems"
    fi
done

# 9. MISCELLANEOUS AND SUPPORT SYSTEMS
echo "# 🔧 MISCELLANEOUS & SUPPORT SYSTEMS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Search for other significant systems
find "$BASE_DIR" \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" \) -type f -size +10000c -exec grep -l -i -E "manager|controller|service|handler" {} \; | while read file; do
    basename_file=$(basename "$file")

    # Skip already cataloged files
    if ! grep -q "$file" "$OUTPUT_FILE" 2>/dev/null; then
        catalog_system "$file" "SUPPORT SYSTEM: $basename_file" "Supporting system component with management or control functionality"
    fi
done

# 10. SUMMARY STATISTICS
echo "# 📊 COMPLETE SYSTEM STATISTICS" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

total_systems=$(grep -c "^## " "$OUTPUT_FILE")
total_files=$(grep -c "**FILE:**" "$OUTPUT_FILE")
dashboard_systems=$(grep -c "DASHBOARD" "$OUTPUT_FILE")
database_systems=$(grep -c "DATABASE\|ROLLUP" "$OUTPUT_FILE")
emotional_systems=$(grep -c "EMOTIONAL" "$OUTPUT_FILE")
letter_systems=$(grep -c "LETTER" "$OUTPUT_FILE")
security_systems=$(grep -c "SECURITY" "$OUTPUT_FILE")
interactive_systems=$(grep -c "INTERACTIVE" "$OUTPUT_FILE")

echo "## System Categories Found:" >> "$OUTPUT_FILE"
echo "- **Total Systems:** $total_systems" >> "$OUTPUT_FILE"
echo "- **Total Files:** $total_files" >> "$OUTPUT_FILE"
echo "- **Dashboard Systems:** $dashboard_systems" >> "$OUTPUT_FILE"
echo "- **Database/Tracking Systems:** $database_systems" >> "$OUTPUT_FILE"
echo "- **Emotional Intelligence Systems:** $emotional_systems" >> "$OUTPUT_FILE"
echo "- **Letter Template Systems:** $letter_systems" >> "$OUTPUT_FILE"
echo "- **Security/Monitoring Systems:** $security_systems" >> "$OUTPUT_FILE"
echo "- **Interactive Content Systems:** $interactive_systems" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "## Critical Missing Systems (Legacy → v4.0):" >> "$OUTPUT_FILE"
echo "1. **Progress Dashboard Manager** (608 lines) - Advanced dashboard visualization" >> "$OUTPUT_FILE"
echo "2. **Synced Rollup Manager** (587 lines) - Cross-database synchronization" >> "$OUTPUT_FILE"
echo "3. **17 Letter Template System** - Complete letter templates with toggle functionality" >> "$OUTPUT_FILE"
echo "4. **40 Executor Task System** - Detailed executor task descriptions" >> "$OUTPUT_FILE"
echo "5. **Security/Audit Systems** - Monitoring and compliance components" >> "$OUTPUT_FILE"
echo "6. **Onboarding Workflow Systems** - User setup and configuration wizards" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "- **Catalog Completed:** $(date)" >> "$OUTPUT_FILE"

echo "=== COMPLETE SYSTEM CATALOGING FINISHED ==="
echo "Results saved to: $OUTPUT_FILE"
echo "Found $total_systems systems across $total_files files"