
```mermaid
flowchart TD
  %% ====== TOP ======
  A[Welcome & Orientation]

  subgraph ONB[Onboarding & Navigation]
    A1[Quick-Start Wizard]
    A2[Mermaid Visual Sitemap]
    A3[First 24–72 Hours Playbook]
    A4[Executor Console]
    A5[Key Contacts & Roles]
  end

  A --> ONB

  %% ====== CHECKLIST HUB ======
  M[Master To-Do List (Hub)]
  A --> M

  %% ====== LEGAL & PRACTICAL DOCS ======
  subgraph LEGAL[Legal & Practical Docs]
    L1[Sample Will]
    L2[Advance Care Directives]
    L3[Accounts & Access]
    L4[Document Locator & Vault Index]
    L5[Assets & Liabilities Inventory]
    L6[Insurance Center]
    L7[Employment & Benefits]
    L8[Subscriptions & Bills Tracker]
    L9[Household Operations Binder]
  end
  M --> LEGAL

  %% ====== CARE PLANS ======
  subgraph CARE[Care Plans]
    C1[Dependents & Care Instructions]
    C2[Pet Care Plan]
  end
  M --> CARE

  %% ====== FUNERAL & MEMORIAL ======
  subgraph FUN[Funeral & Memorial Planning]
    F1[Service Preferences]
    F2[Music & Readings]
    F3[Memorial Program Builder]
  end
  M --> FUN

  %% ====== OBITUARY ======
  O[Obituary Builder (Templates: Formal/Poetic/Humorous)]
  M --> O

  %% ====== LETTERS & REFLECTIONS ======
  subgraph LET[Letters & Reflections (Memory Keeper)]
    R1[Letters to Loved Ones]
    R2[Reflections & Lessons]
    R3[Favorite Memories]
    R4[Legacy Message Scheduler]
  end
  M --> LET

  %% ====== DIGITAL LEGACY ======
  subgraph DIG[Digital Legacy]
    D1[Apple Digital Legacy Guide]
    D2[Google Inactive Account Manager]
    D3[Facebook/Instagram Memorialization]
    D4[Password Manager Setup & Handover]
  end
  M --> DIG

  %% ====== GUIDES & AI ======
  G[Guidance Library (How‑to Pages)]
  X[Compose & Export Center]
  P[Page‑Level AI Prompt Library]
  M --> G
  M --> X
  M --> P

  %% ====== LOCALIZATION & CULTURE ======
  subgraph LOC[Localization & Culture]
    Z1[Localization Toolkit]
    Z2[Cultural/Religious Rites Library]
  end
  M --> LOC

  %% ====== TRUST & SAFETY ======
  subgraph TRUST[Trust, Privacy & Safety]
    T1[Privacy & Security Guide]
    T2[Backup & Offline Pack]
    T3[Legal Disclaimer & Jurisdiction Notes]
  end
  M --> TRUST

  %% ====== SUPPORT ======
  subgraph SUP[Support & Maintenance]
    S1[Help & FAQ]
    S2[Changelog & Version Notes]
  end
  M --> SUP

  %% ====== DESIGN & SAMPLES ======
  subgraph DESIGN[Design System]
    Y1[Style & Design Layer]
    Y2[Design Customization Kit]
  end
  SD[Sample Data Set]
  M --> DESIGN
  M --> SD
```
