# Complete Guide to Notion Block Types for YAML Configuration
## All Supported Content Block Types in the Notion Template v4.0 System

This document describes ALL content block types that can be used in YAML files and are parseable by the deploy.py script. Each entry includes the YAML syntax, actual examples from working files, and what the deploy.py creates in Notion.

---

## 📝 TEXT CONTENT BLOCKS

### 1. Heading 1 (heading_1)
**Purpose**: Main section headers
**YAML Format**:
```yaml
- type: heading_1
  content: "Main Section Title"
```
**Real Example** (from 25_digital_legacy.yaml):
```yaml
- type: heading_1
  content: Google Inactive Account Manager Setup
```
**Deploy.py Processing**: Lines 1418-1423

### 2. Heading 2 (heading_2)
**Purpose**: Subsection headers
**YAML Format**:
```yaml
- type: heading_2
  content: "Subsection Title"
```
**Real Example** (from 25_digital_legacy.yaml):
```yaml
- type: heading_2
  content: Steps to Configure
```
**Deploy.py Processing**: Lines 1424-1429

### 3. Heading 3 (heading_3)
**Purpose**: Sub-subsection headers
**YAML Format**:
```yaml
- type: heading_3
  content: "Sub-subsection Title"
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1430-1435

### 4. Paragraph (paragraph)
**Purpose**: Regular text content
**YAML Format**:
```yaml
- type: paragraph
  content: "Your paragraph text here"
```
**Real Example** (from 25_digital_legacy.yaml):
```yaml
- type: paragraph
  content: Google allows you to decide what happens to your data if your account becomes inactive.
```
**Deploy.py Processing**: Lines 1436-1441

### 5. Quote (quote)
**Purpose**: Quoted text with optional attribution
**YAML Format**:
```yaml
- type: quote
  content: "The quoted text"
  author: "Attribution (optional)"
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1767-1781

---

## 📋 LIST BLOCKS

### 6. Bulleted List Item (bulleted_list_item)
**Purpose**: Individual bullet points
**YAML Format**:
```yaml
- type: bulleted_list_item
  content: "List item text"
```
**Real Example** (from 25_digital_legacy.yaml):
```yaml
- type: bulleted_list_item
  content: Gmail messages and attachments
```
**Deploy.py Processing**: Lines 1442-1447

### 7. Bulleted List (bulleted_list)
**Purpose**: Multiple bullet points as array
**YAML Format**:
```yaml
- type: bulleted_list
  items:
    - "First item"
    - "Second item"
    - "Third item"
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1448-1458, 1549-1572

### 8. Numbered List Item (numbered_list_item)
**Purpose**: Individual numbered items
**YAML Format**:
```yaml
- type: numbered_list_item
  content: "Step or numbered item"
```
**Real Example** (from 25_digital_legacy.yaml):
```yaml
- type: numbered_list_item
  content: Go to myaccount.google.com/inactive
```
**Deploy.py Processing**: Lines 1459-1464

### 9. Numbered List (numbered_list)
**Purpose**: Multiple numbered items as array
**YAML Format**:
```yaml
- type: numbered_list
  items:
    - "First step"
    - "Second step"
    - "Third step"
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1573-1593

### 10. To-Do Item (to_do)
**Purpose**: Checkable task items
**YAML Format** (Simple):
```yaml
- type: to_do
  content: "Task description"
  checked: false
```
**YAML Format** (Complex from executor tasks):
```yaml
- type: to_do
  to_do:
    rich_text:
      - type: text
        text:
          content: "Locate will and death certificate [Time: 2-4 hours] [Priority: Immediate]"
    checked: false
```
**Real Example** (from 11_executor_task_profiles.yaml):
```yaml
- type: to_do
  to_do:
    rich_text:
      - type: text
        text:
          content: "Secure home, pets, vehicles, valuables [Time: 2-6 hours] [Priority: Immediate]"
    checked: false
```
**Deploy.py Processing**: Lines 1505-1548

---

## 🎯 SPECIAL BLOCKS

### 11. Callout (callout)
**Purpose**: Highlighted information boxes with icons
**YAML Format**:
```yaml
- type: callout
  icon: emoji:💡    # or just 💡
  content: "Important information here"
  color: blue_background    # Options: gray, brown, orange, yellow, green, blue, purple, pink, red + _background
```
**Real Example** (from 25_digital_legacy.yaml):
```yaml
- type: callout
  icon: emoji:⚠️
  content: Important - Update your trusted contacts annually to ensure current information
  color: yellow_background
```
**Deploy.py Processing**: Lines 1465-1472

### 12. Toggle (toggle)
**Purpose**: Collapsible sections with nested content
**YAML Format**:
```yaml
- type: toggle
  content: "Click to expand"
  blocks:    # or 'children' - both work
    - type: paragraph
      content: "Hidden content"
    - type: bulleted_list_item
      content: "Hidden bullet point"
```
**Real Example** (from 11_executor_task_profiles.yaml):
```yaml
- type: toggle
  content: "🟦 Simple Estate Workflow (< $500K, basic assets)"
  blocks:
    - type: paragraph
      content: "For estates with straightforward assets: primary residence, basic investments, simple family structure."
    - type: bulleted_list_item
      content: "Estimated total time: 20-40 hours over 3-6 months"
```
**Deploy.py Processing**: Lines 1473-1495

### 13. Divider (divider)
**Purpose**: Horizontal line separator
**YAML Format**:
```yaml
- type: divider
  divider: {}    # Can also just be: - type: divider
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1503-1504

### 14. Code Block (code)
**Purpose**: Formatted code snippets
**YAML Format**:
```yaml
- type: code
  content: "your code here"
  language: javascript    # Optional, defaults to "plain text"
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1496-1502

---

## 🖼️ MEDIA BLOCKS

### 15. Image (image)
**Purpose**: Embedded images
**YAML Format**:
```yaml
- type: image
  url: "https://example.com/image.jpg"    # or 'src' or 'image_url'
  caption: "Image description"    # or 'alt'
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1700-1715

### 16. File (file)
**Purpose**: File attachments
**YAML Format**:
```yaml
- type: file
  url: "https://example.com/document.pdf"    # or 'file_url'
  name: "Document Name"    # or 'filename'
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1717-1732

### 17. PDF (pdf)
**Purpose**: Embedded PDF viewer
**YAML Format**:
```yaml
- type: pdf
  url: "https://example.com/document.pdf"    # or 'pdf_url'
  title: "PDF Document Title"
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1734-1749

### 18. Bookmark (bookmark)
**Purpose**: Web link preview
**YAML Format**:
```yaml
- type: bookmark
  url: "https://example.com"    # or 'link'
  caption: "Website description"    # or 'title'
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1751-1765

### 19. Embed (embed)
**Purpose**: Embedded external content (YouTube, Twitter, etc.)
**YAML Format**:
```yaml
- type: embed
  url: "https://youtube.com/watch?v=..."
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1594-1609

---

## 📊 ADVANCED BLOCKS

### 20. Table (table)
**Purpose**: Data tables
**YAML Format**:
```yaml
- type: table
  has_header: true    # Optional, default true
  has_row_header: false    # Optional, default false
  rows:
    - cells: ["Header 1", "Header 2", "Header 3"]
    - cells: ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"]
    - cells: ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"]
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1610-1650

### 21. Child Database (child_database)
**Purpose**: Inline database view
**YAML Format**:
```yaml
- type: child_database
  title: "Database Title"
  database_id: "database-uuid"    # Optional
  database_ref: "Database Name"    # Alternative to ID
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1651-1679

### 22. Linked Database (linked_db)
**Purpose**: Reference to existing database
**YAML Format**:
```yaml
- type: linked_db
  linked_db: "Database Name"
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1680-1699

### 23. Link to Page (link_to_page)
**Purpose**: Link to another Notion page
**YAML Format**:
```yaml
- type: link_to_page
  page_id: "page-uuid"    # or 'target_page_id'
  title: "Page Title"    # or 'page_title'
```
**Real Example**: Not found in current YAMLs but supported
**Deploy.py Processing**: Lines 1797-1817

### 24. Column List (column_list)
**Purpose**: Multi-column layout (partially supported)
**YAML Format**:
```yaml
- type: column_list
  columns:
    - blocks: [...]    # Column 1 content
    - blocks: [...]    # Column 2 content
```
**Real Example**: Not found in current YAMLs
**Deploy.py Processing**: Lines 1783-1795 (flattens to paragraph currently)

---

## 🔧 SPECIAL YAML STRUCTURES

### Database Properties (not blocks, but related)
These appear in database definitions, not page blocks:
```yaml
databases:
  - title: "Database Name"
    properties:
      Field_Name:
        type: title    # or rich_text, number, select, multi_select, checkbox, formula
```
**Real Example** (from 11_executor_task_profiles.yaml):
```yaml
Task_Name:
  type: title
  title: {}
Estate_Complexity:
  type: select
  select:
    options:
      - name: "Simple"
        color: "blue"
```

---

## 📝 AUTO-GENERATED BLOCKS

The deploy.py script also auto-generates these blocks from page metadata when no blocks are defined (lines 794-838):

### From Description Field
```yaml
description: "Page description text"
```
Becomes:
```yaml
- type: paragraph
  content: "Page description text"
```

### From Disclaimer Field
```yaml
disclaimer: "Legal disclaimer text"
```
Becomes:
```yaml
- type: callout
  icon: ⚠️
  content: "Legal disclaimer text"
  color: yellow_background
```

### From Role Field
```yaml
role: owner    # or executor, family
```
Becomes:
```yaml
- type: callout
  icon: 👤
  content: "This section is for the estate owner to prepare."
  color: blue_background
```

### From Prompt Field
```yaml
Prompt: "Instructions for the user"
```
Becomes:
```yaml
- type: toggle
  content: "📝 Instructions"
  blocks:
    - type: paragraph
      content: "Instructions for the user"
```

---

## 🚫 WHAT'S LEFT OUT AND WHY

### 1. Synced Blocks
**Reason**: Not found in any YAML files, requires complex cross-page reference management. The deploy.py mentions synced blocks in comments but doesn't implement them.

### 2. Mention Blocks (@mentions)
**Reason**: Requires user/page IDs that aren't available at YAML creation time. Would need runtime resolution.

### 3. Equation Blocks
**Reason**: Not implemented in deploy.py, not found in any YAML files. Would require LaTeX/KaTeX support.

### 4. Video Blocks (native)
**Reason**: While embed blocks can handle YouTube, native video upload blocks aren't supported. Would require file hosting.

### 5. Audio Blocks
**Reason**: Not implemented in deploy.py, not part of standard Notion API block types.

### 6. Template Button Blocks
**Reason**: Complex interactive elements that require template configuration. Not found in YAMLs.

### 7. Breadcrumb Blocks
**Reason**: Automatically generated by Notion, can't be created via API.

### 8. Table of Contents Blocks
**Reason**: While Notion supports these, they're not implemented in deploy.py and not found in YAMLs.

### 9. Child Page Blocks
**Reason**: Pages are created separately through the page hierarchy, not as blocks within other pages.

### 10. Database Row Blocks
**Reason**: Database entries are created through different API endpoints, not as page blocks.

### 11. Complex Rich Text Formatting
**Reason**: The current implementation only supports plain text in blocks. Advanced formatting like:
- Bold, italic, underline, strikethrough
- Inline code
- Colors and highlights
- Links within text
These would require rich_text array modifications not currently in the YAMLs.

### 12. Column Layouts (partial support)
**Reason**: While column_list is recognized in deploy.py (lines 1783-1795), it currently just creates a placeholder paragraph because proper column implementation requires special parent-child block relationships not fully supported.

---

## 📌 USAGE NOTES

1. **Block Order**: Blocks appear in Notion in the order they're listed in the YAML file
2. **Nesting**: Only `toggle` blocks support nested content via the `blocks` or `children` field
3. **Variable Substitution**: The deploy.py supports variable substitution in content fields (lines 54-102)
4. **Multi-block Returns**: Some block types (bulleted_list, numbered_list with items) return multiple blocks
5. **Fallbacks**: Invalid block structures often fallback to paragraph blocks with error messages
6. **Color Options**: For callouts: gray, brown, orange, yellow, green, blue, purple, pink, red (append _background)
7. **Emoji Format**: Can use either `emoji:📝` or just `📝` format

---

## 🎯 BEST PRACTICES

1. **Use Appropriate Headers**: heading_1 for main sections, heading_2 for subsections
2. **Group Related Items**: Use toggle blocks to hide detailed content
3. **Highlight Important Info**: Use callouts with appropriate colors (yellow for warnings, blue for info)
4. **Structure Tasks**: Use to_do blocks for actionable items
5. **Maintain Consistency**: Use the same block patterns across similar pages
6. **Test Complex Structures**: Toggles with nested content and tables should be tested
7. **Document Fallbacks**: Some blocks (like column_list) don't fully work and fallback to text

---

*This guide is based on analysis of deploy.py (lines 1418-1817) and all YAML files in split_yaml/ directory. Last updated based on v4.0 Production codebase.*