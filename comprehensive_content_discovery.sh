#!/bin/bash

# Comprehensive Content Discovery Script
# Searches for missing content patterns in all files under /Users/jonathanhollander/AI Code/Notion Template

BASE_DIR="/Users/jonathanhollander/AI Code/Notion Template"
OUTPUT_FILE="COMPREHENSIVE_CONTENT_DISCOVERY_RESULTS.md"
TEMP_YAML_TERMS="temp_yaml_terms.txt"

echo "# Comprehensive Content Discovery Results" > "$OUTPUT_FILE"
echo "Date: $(date)" >> "$OUTPUT_FILE"
echo "Search Location: $BASE_DIR" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Function to add matches to output with full context
add_match() {
    local file="$1"
    local line_num="$2"
    local pattern="$3"
    local context="$4"

    echo "## MATCH FOUND" >> "$OUTPUT_FILE"
    echo "**FILE:** $file" >> "$OUTPUT_FILE"
    echo "**LINE:** $line_num" >> "$OUTPUT_FILE"
    echo "**PATTERN:** \"$pattern\"" >> "$OUTPUT_FILE"
    echo "**CONTEXT:**" >> "$OUTPUT_FILE"
    echo "\`\`\`" >> "$OUTPUT_FILE"
    echo "$context" >> "$OUTPUT_FILE"
    echo "\`\`\`" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

echo "=== PHASE 1: Extracting YAML Terms ==="

# Extract all unique terms from existing YAML files for reference
find "$BASE_DIR" -name "*.yaml" -o -name "*.yml" | while read yaml_file; do
    # Extract field names and values
    grep -E "^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:" "$yaml_file" | sed 's/:.*//' | sed 's/^\s*//' >> "$TEMP_YAML_TERMS"
    grep -E "^\s*-\s+" "$yaml_file" | sed 's/^\s*-\s*//' >> "$TEMP_YAML_TERMS"
done

# Remove duplicates and sort
sort "$TEMP_YAML_TERMS" | uniq > "${TEMP_YAML_TERMS}.clean"
mv "${TEMP_YAML_TERMS}.clean" "$TEMP_YAML_TERMS"

echo "Extracted $(wc -l < "$TEMP_YAML_TERMS") unique YAML terms"

echo "=== PHASE 2: Comprehensive Pattern Search ==="

# Define all search patterns
declare -a PATTERNS=(
    # Database & Tracking
    "database" "formulae" "formula" "tracking" "status" "completion" "station"
    "rollup" "relation" "select" "checkbox" "progress" "metrics" "properties"

    # Emotional Intelligence & EQ
    "emotional intelligence" "EQ" "empathy" "compassion" "grief" "bereavement"
    "emotional support" "sensitivity" "comfort" "care" "understanding" "loss"
    "gentle" "supportive" "kindness" "family dynamics"

    # Letters & Communication
    "letter" "template" "draft" "body" "disclaimer" "prompt" "audience"
    "notification" "correspondence" "bank" "utility" "insurance"

    # Prompts & Guidance
    "prompts" "instructions" "guidance" "user guidance" "template prompts"
    "help text" "tooltips" "explanations" "directions"

    # Interactive Content
    "toggle" "expand" "collapse" "accordion" "show/hide" "details"
    "summary" "more info" "dropdown" "reveal"

    # General & Miscellaneous
    "general items" "miscellaneous" "support systems"
    "additional" "extra" "other" "various"

    # Dashboard & Visualization
    "dashboard" "grid" "analytics" "visualization" "gauge" "chart"
    "burndown" "progress bar" "status indicator"
)

# Search for each pattern in all target file types
echo "# Pattern Search Results" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

total_matches=0

for pattern in "${PATTERNS[@]}"; do
    echo "Searching for pattern: $pattern"

    # Search in all target file types with context
    find "$BASE_DIR" \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.txt" -o -name "*.md" \) -type f | while read file; do
        # Search for pattern with line numbers and context
        grep -n -i -B2 -A2 "$pattern" "$file" 2>/dev/null | while IFS=: read line_num content; do
            if [[ "$line_num" =~ ^[0-9]+$ ]]; then
                # Get 5 lines of context around the match
                context=$(sed -n "$((line_num-2)),$((line_num+2))p" "$file" | sed "${line_num}s/^/→ /")
                add_match "$file" "$line_num" "$pattern" "$context"
                ((total_matches++))
            fi
        done
    done
done

echo "=== PHASE 3: YAML Term Cross-Reference ==="

echo "# YAML Term Cross-Reference" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Check if any YAML terms appear in other files with additional context
while read yaml_term; do
    if [[ -n "$yaml_term" && ${#yaml_term} -gt 2 ]]; then
        find "$BASE_DIR" \( -name "*.py" -o -name "*.json" -o -name "*.txt" -o -name "*.md" \) -type f | while read file; do
            grep -n -i -B1 -A1 "$yaml_term" "$file" 2>/dev/null | while IFS=: read line_num content; do
                if [[ "$line_num" =~ ^[0-9]+$ ]]; then
                    context=$(sed -n "$((line_num-1)),$((line_num+1))p" "$file" | sed "${line_num}s/^/→ /")
                    add_match "$file" "$line_num" "YAML-TERM: $yaml_term" "$context"
                fi
            done
        done
    fi
done < "$TEMP_YAML_TERMS"

echo "=== PHASE 4: Summary Generation ==="

echo "# Summary Statistics" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "- **Total Matches Found:** $total_matches" >> "$OUTPUT_FILE"
echo "- **Search Patterns Used:** ${#PATTERNS[@]}" >> "$OUTPUT_FILE"
echo "- **YAML Terms Cross-Referenced:** $(wc -l < "$TEMP_YAML_TERMS")" >> "$OUTPUT_FILE"
echo "- **Search Completed:** $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Generate file statistics
echo "# Files with Most Matches" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
grep "**FILE:**" "$OUTPUT_FILE" | sort | uniq -c | sort -nr | head -20 >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Clean up temp files
rm -f "$TEMP_YAML_TERMS"

echo "=== CONTENT DISCOVERY COMPLETE ==="
echo "Results saved to: $OUTPUT_FILE"
echo "Total matches found: $total_matches"