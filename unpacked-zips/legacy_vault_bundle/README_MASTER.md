# Comprehensive Legacy Vault — Master README
Date: 2025-08-22

This bundle contains **CSV databases** ready to import into Notion and **Markdown pages** to paste as template pages.
After importing, set relations and duplicate views as described below.

## Contents
- CSVs (12): contacts_roles, legal_documents, financial_assets, subscriptions_bills, digital_accounts, executor_tasks, medical_meds, final_wishes, heirlooms, messages_loved_ones, memories_stories, executor_expenses
- Markdown guides/templates:
  - HOW_TO_USE.md
  - MASTER_CHECKLIST.md
  - EXECUTOR_QUICK_SHEET.md
  - SAMPLE_WILL.md (educational sample; NOT legal advice)
  - EXECUTOR_EMAIL_TEMPLATES.md
  - DIGITAL_LEGACY_CENTER_SAMPLE.md
  - DIGITAL_GUARDIAN_SETUP_GUIDE.md
  - STORY_PROMPTS.md
  - ETHICAL_WILL_TEMPLATE.md

## Import steps (Notion)
1. Create a new page called **Legacy Vault (Master)**.
2. For each CSV in this bundle, create a new inline table and **Import** the corresponding CSV file.
3. Rename each database to match its CSV name (or your preferred names).
4. Set the following **Relations**:
   - **Messages to Loved Ones → Recipient** → **Contacts & Roles**
   - **Memories & Stories → People** → **Contacts & Roles**
   - **Heirlooms → Intended Recipient** → **Contacts & Roles**
5. On **Contacts & Roles**, add Rollups:
   - Messages Count (count of related Messages)
   - Memories Count (count of related Memories)
   - Heirlooms Count (count of related Heirlooms)
6. Create **Views** per the HOW_TO_USE.md quick guide.
7. Add **Template Buttons** using the prompts in HOW_TO_USE.md.
8. Paste the Markdown files here as new Notion pages under the appropriate sections.
9. Mark or delete all rows titled **“EXAMPLE — …”** as you replace them with real data.

## Disclaimer
- **No legal advice** is provided. The SAMPLE_WILL.md is an educational example only.
- Account automations (like inactivity triggers) are the user’s responsibility. See DIGITAL_GUARDIAN_SETUP_GUIDE.md.
