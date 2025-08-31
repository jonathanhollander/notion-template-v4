# Estate Planning Concierge v4.0 - Comprehensive Feature-to-YAML Mapping

## Executive Summary
This document maps every feature in the Estate Planning Concierge v4.0 to its corresponding YAML configuration file. The system comprises 22 YAML files that define pages, databases, letters, UI elements, and administrative features.

## Core Architecture Files

### 00_admin.yaml
**Features:**
- Admin Release Notes page (version history)
- Admin Rollout Cockpit (setup guidance with acceptance DB)
- Admin Diagnostics page (missing icons/covers checks)
- Admin Final UI Checklist (premium UI polish verification)
- Helper instructions for each admin page
- Role-based access control (owner role)

### 00_copy_registry.yaml
**Features:**
- Centralized copy/description registry for consistent messaging
- Hub descriptions (Preparation, Executor, Family)
- Legal document disclaimers
- QR code descriptions
- Insurance and subscription guidance text

### 01_pages_core.yaml
**Features:**
- **Three Main Hubs:**
  - Preparation Hub (owner role, personal starting place)
  - Executor Hub (executor role, resource center)
  - Family Hub (family role, gentle guidance)
- **Top-Level Pages:**
  - Legal Documents (samples, disclaimers)
  - Financial Accounts (banks, cards, brokerages)
  - Property & Assets (homes, vehicles, digital)
  - Insurance (life, home, health, auto)
  - Subscriptions (utilities, streaming, services)
  - Letters (ready-to-adapt templates)
  - Memories & Keepsakes (photos, stories)
  - Contacts (key people and organizations)
  - QR Codes (printable access points)
- **Nested Legal Documents:**
  - Living Will Sample
  - Power of Attorney Sample
  - Advance Directive Sample
  - Trust Sample Outline
- **Nested Financial Pages:**
  - Primary Bank Accounts
  - Credit Cards
  - Brokerage & Retirement
- **Nested Property Pages:**
  - Real Estate
  - Vehicles
  - Digital Assets
- **Nested Insurance Pages:**
  - Life Insurance
  - Homeowners/Renters
  - Health Insurance
- **QR Code Pages:**
  - QR Family Essentials
  - QR Full Access for Executor

### 02_pages_extended.yaml
**Features:**
- **40 Executor Tasks** (Task 01-40, standardized format)
- **9 Executor Guides:**
  - SSA Notification
  - IRS Final Return Notes
  - DMV Title Transfer
  - USPS Mail Forwarding
  - Mortgage Servicer
  - Landlord/HOA
  - Pension/401(k) Administrator
  - Brokerage Transfer
  - Credit Bureaus (Equifax/Experian/TransUnion)
- **6 Digital Asset Pages:**
  - Passwords & Access Hints
  - Email Accounts
  - Cloud Storage
  - Photo Archives
  - Domain Names
  - Crypto Wallets
- **4 Family Memorial Pages:**
  - Letters of Sympathy
  - Memorial Playlist
  - Photo Collage Plan
  - Memorial Guestbook

### 03_letters.yaml
**Features:**
- **18 Letter Templates:**
  - Bank Notification (deceased account holder)
  - Credit Card Closure Request
  - Utility Account Transfer/Closure
  - Insurance Claim Notification
  - Employer HR Notification
  - Subscription Cancellation
  - Social Media Memorialization
  - SSA Notification of Death
  - IRS Final Return & Estate EIN
  - DMV Title Transfer Request
  - USPS Mail Forwarding for Estate
  - Mortgage Servicer Notice
  - Landlord/HOA Notification
  - Pension/401(k) Administrator Notice
  - Brokerage Transfer/Beneficiary Claim
  - Credit Bureaus Deceased Flag
  - QR Pack Cover Letters (Family & Executor)
- Each letter includes:
  - Title, Audience, Category
  - Body template with {{placeholders}}
  - Customization prompt
  - Legal disclaimer

### 04_databases.yaml
**Features:**
- **7 Core Databases:**

1. **Accounts Database**
   - Properties: Name, Institution, Type, Account #, Notes, Related Page, Tags
   - Seed data: Bank, Retirement, Brokerage accounts (8 entries)
   - Tags: Critical, Tax, Transfer, Beneficiaries

2. **Property Database**
   - Properties: Name, Type, Identifier, Notes
   - Seed data: Primary Residence, Vehicle, Safe Deposit Box

3. **Insurance Database**
   - Properties: Policy, Carrier, Type, Policy #, Notes, Related Page, Tags
   - Seed data: Life, Health, Home, Auto insurance

4. **Contacts Database**
   - Properties: Name, Role, Email, Phone, Notes, Tags
   - Seed data: Attorney, Executor, Accountant, Family Contact
   - Tags: Legal, Executor, Finance, Family, Urgent

5. **Subscriptions Database**
   - Properties: Service, Category, Account Email, Notes, Tags
   - Seed data: Utilities, Digital Services, Memberships

6. **Keepsakes Database**
   - Properties: Title, Story, Where, Tags
   - Seed data: Photos, Stories, Letters

7. **Letters Index Database**
   - Properties: Title, Audience, Category, URL, Related Page
   - Seed data: 10 letter references
   - Categories: Banking, Credit Cards, Utilities, Insurance, etc.

### 08_ultra_premium_db_patch.yaml
**Features:**
- **4 New Advanced Databases:**
  1. **Transactions** (Date, Amount, Type, Archive Flag formula)
  2. **Property Maintenance Logs** (Date, Cost, Category, Vendor)
  3. **Insurance Claims** (Claim #, Status, Date Filed, Amount)
  4. **Estate Analytics** (Rollup formulas for total estate value, tax liability, progress bars)
- **Property Patches for Existing DBs:**
  - Accounts: Archive Flag, Progress Bar formulas
  - Properties: Archive Flag, Progress Bar formulas
  - Insurance: Archive Flag, Progress Bar formulas
- **Seed Data:** Sample transactions, maintenance logs, claims

### 09_admin_rollout_setup.yaml
**Features:**
- Admin Rollout page (setup workspace)
- Admin Rollup Setup Guide (configure UI rollups)
- Admin Views Setup Guide (create saved views)
- Admin QA Checklist (final verification)
- **Acceptance DB Rows:**
  - UI rollup configuration tasks
  - View creation tasks
  - Hub verification tasks

### 10_personalization_settings.yaml
**Features:**
- Admin Settings page
- Estate Complexity selector (Simple/Moderate/Complex)
- Personalization guidance
- Setup & Acceptance DB property patch (Estate Complexity field)

### 11_executor_task_profiles.yaml
**Features:**
- Executor Task Packs page
- **3 Complexity-Based Task Packs:**
  1. **Simple Estate Pack** (5 basic tasks)
  2. **Moderate Estate Pack** (10 tasks including insurance)
  3. **Complex Estate Pack** (15+ tasks including business/tax)
- Each pack as checklist (to_do blocks)

### 12_letters_content_patch.yaml
**Features:**
- Expanded letter content for 3 key letters:
  - Credit Card Company Notification
  - Bank Account Transition/Closure
  - Utility Provider Service Change
- Full body templates with placeholders
- Specific disclaimers per letter type

### 13_hub_ui_embeds.yaml
**Features:**
- Hub UI enhancement markers
- **Preparation Hub:** Setup & Acceptance view embed
- **Executor Hub:** Executor Tasks & Insurance Claims embeds
- **Family Hub:** Letters Outbox view embed
- Progress snapshot callouts

### 14_assets_standardization.yaml
**Features:**
- Asset file path standardization
- Icon file paths (SVG format)
- Cover file paths (SVG format)
- PNG fallback paths for mobile
- Consistent naming convention

### 15_mode_guidance.yaml
**Features:**
- Mode-specific guidance system
- Context-aware helper text
- Role-based content display
- Progressive disclosure patterns

### 16_letters_database.yaml
**Features:**
- **Letters Database Schema:**
  - Properties: Name, Recipient Type, Purpose, Recipient Name, Related Account, Body, Disclaimer, Status, Last Sent
  - Status options: Draft, Ready, Sent, Follow-up Needed
- **Letters Library (Pages):** Parallel page structure for letters
- **3 Detailed Letter Seeds** with full content

### 17_hub_copy_polish.yaml
**Features:**
- Hub copy refinement
- Compassionate language updates
- Role-specific messaging
- Empathy-driven content

### 18_admin_helpers_expanded.yaml
**Features:**
- Expanded admin helper content
- Step-by-step setup instructions
- Troubleshooting guidance
- Best practices documentation

### 19_assets_standardize_patch.yaml
**Features:**
- Asset standardization patches
- Icon/cover file consolidation
- Path normalization
- Mobile-friendly PNG alternatives

### 20_blueprints.yaml
**Features:**
- **View Blueprints:**
  - Accounts Active Only view
  - Letters Drafts view
- **Rollup Blueprints:**
  - Estate Liquid Assets Sum
- Filter and sort configurations

### 99_release_notes.yaml
**Features:**
- Complete version history (v0.0 to v3.6.2)
- Feature evolution tracking
- Major milestone documentation
- Technical improvements log

### builders_console.yaml
**Features:**
- Builder's Console admin page
- Diagnostics overview section
- Acceptance by section tracking
- Linked database views
- Setup completion verification

### zz_acceptance_rows.yaml
**Features:**
- **62 Acceptance Tasks** covering:
  - 12 Top Level pages
  - 4 Legal Documents
  - 7 Executor Hub items
  - 2 Family Hub items
  - 3 Financial Accounts
  - 3 Property & Assets
  - 3 Insurance sections
  - 3 Subscriptions
  - 2 QR Codes
  - 7 Letters
  - 7 Database Setup tasks
- Each task includes:
  - Page name, Role, Check description
  - Status (Pending), Est. Time, Section

## Feature Categories Summary

### 1. **Page Structure (100+ pages total)**
- 3 Main Hubs
- 12 Top-level pages
- 40+ Executor tasks
- 9 Executor guides
- 6 Digital asset pages
- 4 Family memorial pages
- 18 Letter templates
- 4 Admin pages

### 2. **Database Architecture (11 databases)**
- 7 Core databases (Accounts, Property, Insurance, Contacts, Subscriptions, Keepsakes, Letters Index)
- 4 Advanced databases (Transactions, Property Maintenance, Insurance Claims, Estate Analytics)

### 3. **Letters System**
- 18 Pre-written letter templates
- Database-driven letter management
- Status tracking (Draft/Ready/Sent)
- Placeholder system for personalization

### 4. **Administrative Features**
- Setup & Acceptance tracking
- Rollout cockpit
- Diagnostics system
- QA checklist
- Estate complexity settings
- View blueprints

### 5. **UI/UX Features**
- Role-based access (owner/executor/family)
- Progress bars and completion tracking
- Archive flags for completed items
- Embedded database views in hubs
- Mobile-friendly PNG icons/covers
- Synced blocks for consistency

### 6. **Automation & Formulas**
- Estate value calculations
- Tax liability formulas
- Progress percentage calculations
- Archive flag automations
- Rollup aggregations

### 7. **Personalization System**
- Estate complexity profiles (Simple/Moderate/Complex)
- Task pack selection
- Copy registry for consistent messaging
- Helper toggle system

## Critical Integration Points

1. **Related Page Relations:** Connect databases to page hierarchy
2. **Rollup Properties:** Aggregate financial data across databases
3. **Formula Dependencies:** Progress bars depend on completion percentages
4. **View Filters:** Archive flags control visibility
5. **Section Organization:** Pages organized by role and purpose
6. **Helper System:** One-way removal with idempotent markers

## Deployment Considerations

1. **Order of Operations:**
   - Create pages first (01_pages_core.yaml)
   - Then databases (04_databases.yaml)
   - Apply patches (08_ultra_premium_db_patch.yaml)
   - Configure views (20_blueprints.yaml)
   - Seed data last

2. **API Requirements:**
   - Notion API v2025-09-03 compatibility
   - Rate limiting (2.5 RPS)
   - Relation binding post-creation
   - Formula validation

3. **Validation Points:**
   - All 22 YAML files must load
   - Relations must resolve
   - Formulas must validate
   - Seeds must match schemas

This mapping ensures every feature from chat history and v3.84 intentions is accounted for in the v4.0 production build.