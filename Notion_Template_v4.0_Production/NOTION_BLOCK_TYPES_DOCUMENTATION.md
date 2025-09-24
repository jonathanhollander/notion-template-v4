# Notion Block Types - Implementation Documentation

## Overview
This document provides a comprehensive guide to all Notion block types that can be used in YAML files for the Estate Planning v4.0 deployment system. Each block type has been verified against the implementation in `deploy.py` (as of 2025-09-24).

---

## ✅ IMPLEMENTED BLOCK TYPES (26 Total)

### Text & Heading Blocks

#### 1. **paragraph** (Line 1030)
Basic text paragraph block.
```yaml
blocks:
  - type: paragraph
    content: "This is a paragraph of text"
```

#### 2. **heading_1** (Line 1012)
Level 1 heading - largest heading size.
```yaml
blocks:
  - type: heading_1
    content: "Main Title"
```

#### 3. **heading_2** (Line 1018)
Level 2 heading - medium heading size.
```yaml
blocks:
  - type: heading_2
    content: "Section Title"
```

#### 4. **heading_3** (Line 1024)
Level 3 heading - smallest heading size.
```yaml
blocks:
  - type: heading_3
    content: "Subsection Title"
```

### List Blocks

#### 5. **bulleted_list_item** (Line 1036)
Individual bullet point in a list.
```yaml
blocks:
  - type: bulleted_list_item
    content: "First bullet point"
  - type: bulleted_list_item
    content: "Second bullet point"
```

#### 6. **bulleted_list** (Lines 1043, 1054)
Container for bulleted list items (two implementations for flexibility).
```yaml
blocks:
  - type: bulleted_list
    items:
      - "First item"
      - "Second item"
```

#### 7. **numbered_list_item** (Line 1065)
Individual numbered item in a list.
```yaml
blocks:
  - type: numbered_list_item
    content: "Step 1: Do this first"
  - type: numbered_list_item
    content: "Step 2: Then do this"
```

#### 8. **numbered_list** (Line 1072)
Container for numbered list items.
```yaml
blocks:
  - type: numbered_list
    items:
      - "First step"
      - "Second step"
```

#### 9. **to_do** (Line 1083)
Checkbox/to-do item with checked state.
```yaml
blocks:
  - type: to_do
    content: "Complete this task"
    checked: false
```

### Special Content Blocks

#### 10. **toggle** (Line 1094)
Collapsible/expandable content block.
```yaml
blocks:
  - type: toggle
    content: "Click to expand"
    children:
      - type: paragraph
        content: "Hidden content inside toggle"
```

#### 11. **callout** (Line 1113)
Highlighted box with icon and text.
```yaml
blocks:
  - type: callout
    content: "Important information"
    icon: "⚠️"
    color: "yellow_background"
```

#### 12. **quote** (Line 1304)
Styled quotation block with optional author.
```yaml
blocks:
  - type: quote
    text: "The best time to plant a tree was 20 years ago."
    author: "Chinese Proverb"
```

#### 13. **code** (Line 1133)
Code block with syntax highlighting.
```yaml
blocks:
  - type: code
    content: "print('Hello World')"
    language: "python"
```

#### 14. **divider** (Line 1144)
Horizontal line separator.
```yaml
blocks:
  - type: divider
```

### Media & File Blocks

#### 15. **image** (Line 1237)
External image with optional caption.
```yaml
blocks:
  - type: image
    url: "https://example.com/photo.jpg"
    caption: "Estate planning diagram"
```

#### 16. **file** (Line 1254)
External file attachment.
```yaml
blocks:
  - type: file
    file_url: "https://example.com/document.pdf"
    name: "Estate Planning Guide.pdf"
```

#### 17. **pdf** (Line 1271)
Embedded PDF viewer.
```yaml
blocks:
  - type: pdf
    pdf_url: "https://example.com/will-template.pdf"
    title: "Will Template"
```

#### 18. **embed** (Line 1149)
Embedded external content (iframe).
```yaml
blocks:
  - type: embed
    url: "https://youtube.com/watch?v=xyz"
    caption: "Estate Planning Tutorial"
```

#### 19. **bookmark** (Line 1288)
Web bookmark with preview.
```yaml
blocks:
  - type: bookmark
    url: "https://www.irs.gov/forms"
    title: "IRS Forms and Publications"
```

### Database & Structural Blocks

#### 20. **table** (Line 1164)
Table with rows and cells.
```yaml
blocks:
  - type: table
    has_column_header: true
    has_row_header: false
    rows:
      - cells: ["Asset", "Value", "Beneficiary"]
      - cells: ["House", "$500,000", "Spouse"]
```

#### 21. **child_database** (Line 1195)
Inline database within a page.
```yaml
blocks:
  - type: child_database
    title: "Asset Inventory"
    database_id: "database_123"
```

#### 22. **link_to_page** (Line 1334)
Link to another Notion page.
```yaml
blocks:
  - type: link_to_page
    page_id: "page_789"
    title: "Related Document"
```

#### 23. **column_list** (Line 1320)
Multi-column layout (currently simplified).
```yaml
blocks:
  - type: column_list
    columns:
      - children:
          - type: paragraph
            content: "Left column content"
      - children:
          - type: paragraph
            content: "Right column content"
```

### Navigation & Organization Blocks

#### 24. **child_page** (Line 1356)
Reference to a subpage within current page.
```yaml
blocks:
  - type: child_page
    page_id: "page_123"
    title: "Subpage Title"
    icon: "📄"
```

#### 25. **table_of_contents** (Line 1377)
Automatically generated table of contents from headings.
```yaml
blocks:
  - type: table_of_contents
    color: "blue"  # Optional: default, gray, brown, orange, yellow, green, blue, purple, pink, red
```

#### 26. **breadcrumb** (Line 1389)
Navigation breadcrumb showing page hierarchy.
```yaml
blocks:
  - type: breadcrumb
```

---

## ❌ NOT IMPLEMENTED BLOCK TYPES

Based on Notion API 2025 documentation, the following block types are **NOT** implemented:

### Media Types
1. **video** - Video embeds
   - *Reason:* Not needed for estate planning documents

2. **audio** - Audio file embeds
   - *Reason:* Not relevant for legal documentation

### Advanced Layout
3. **column** - Individual column within column_list
   - *Reason:* Partially implemented within column_list, full support requires complex nested structure handling

4. **synced_block** - Content synced across pages
   - *Reason:* Complex cross-page synchronization not required for template deployment

### External Integrations
5. **link_preview** - Rich link preview
   - *Reason:* Bookmark block provides similar functionality

6. **mention** - @mentions of users/pages/dates
   - *Reason:* Requires user/workspace context not available during deployment

7. **equation** - LaTeX math equations
   - *Reason:* Not needed for estate planning content

### Template Blocks
8. **template** - Reusable content templates
    - *Reason:* Templates are handled at YAML level, not block level

---

## Special Handling Notes

### String Body Fields
Letter templates and other pages with string `Body` fields are automatically converted to paragraph blocks (Lines 685-695):
```yaml
pages:
  - title: Letter to Executor
    Body: |
      Dear Executor,

      This letter provides instructions...
```

### Legacy Format Support
The system automatically converts legacy block formats to current Notion API format (Line 1004).

### Error Handling
All block types with missing required fields (URLs, IDs, etc.) gracefully fallback to paragraph blocks with descriptive placeholders.

### Rich Text Formatting
All text content supports Notion's rich text formatting:
- **Bold**: `**text**`
- *Italic*: `*text*`
- `Code`: `` `text` ``
- Links: `[text](url)`

---

## Usage Examples

### Complete Page with Multiple Block Types
```yaml
pages:
  - title: Estate Planning Guide
    icon: emoji:📋
    blocks:
      - type: heading_1
        content: "Complete Estate Planning Guide"

      - type: callout
        content: "This guide covers all essential estate planning steps"
        icon: "📌"

      - type: heading_2
        content: "Required Documents"

      - type: to_do
        content: "Create will"
        checked: false

      - type: to_do
        content: "Establish trust"
        checked: false

      - type: divider

      - type: heading_2
        content: "Important Resources"

      - type: bookmark
        url: "https://www.irs.gov/forms"
        title: "IRS Tax Forms"

      - type: file
        file_url: "https://example.com/template.pdf"
        name: "Will Template.pdf"

      - type: quote
        text: "The best time to plan is now"
        author: "Estate Planning Expert"
```

---

## Implementation Location Reference
All block type implementations are in `/deploy.py`:
- Main function: `build_block(block_def)` starting at line 998
- Text blocks: Lines 1012-1035
- List blocks: Lines 1036-1082
- Special blocks: Lines 1083-1163
- Database blocks: Lines 1164-1236
- Media blocks: Lines 1237-1354
- Navigation blocks: Lines 1356-1395
- Default handler: Lines 1397-1402

---

*Document generated: 2025-09-24*
*Last implementation update: Added 3 critical navigation block types (child_page, table_of_contents, breadcrumb)*