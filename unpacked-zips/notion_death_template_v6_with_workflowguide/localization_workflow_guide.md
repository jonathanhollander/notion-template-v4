# Localization Workflow Guide

This guide explains how to translate and localize the Premium Notion Template into a new language and culture. 
Follow these steps carefully to ensure consistency, cultural appropriateness, and the supportive psychological tone of the product.

---

## 1. Files You Will Use
- **english_master_document.md** → contains all original English content with Keys.  
- **translator_prompt.md** → contains instructions on how translations must be formatted and adapted.  
- **localization_master.csv** → contains all Keys with English text and empty columns for translations.  
- (Optional) **databases/*.csv** → individual databases with sample data for direct import into Notion.

---

## 2. Translation Process
1. Open `translator_prompt.md`.  
2. Copy the entire contents of `translator_prompt.md` into your translation tool (LLM or human workflow).  
3. Immediately after, paste the contents of `english_master_document.md`.  
4. Run the translation process.

---

## 3. Output Format
The translated output must follow this format for **every entry**:

```
Key: [unique_key]
English: [original English text]
[Target Language]: [translated localized text]
Notes: [explanation of cultural/linguistic/psychological changes, why they were made]
```

---

## 4. Cultural & Psychological Requirements
- Always adapt the **tone** to grieving families in the target culture.  
- Emphasize compassion, reassurance, and calm clarity.  
- Respect cultural norms around death, memory, and legacy:  
  - Family vs. individual focus  
  - Spiritual/religious undertones  
  - Formal vs. informal register  
- Adjust legal/financial terms to local equivalents. Mark differences with `[adapted]`.  
- Maintain consistency of translated terms (use the same word for “executor,” “will,” “memorial program”).  

---

## 5. Reinserting Translations
- Use the bilingual output as a **reference document**.  
- Replace English text in Notion pages with the translated version, guided by Keys.  
- For databases:  
  - Translate directly in `localization_master.csv`.  
  - Save as new CSV and import into Notion (New Database → Import → CSV).  

---

## 6. Quality Check
- Review all Notes for cultural appropriateness.  
- Verify tone is calm, premium, and supportive (not clinical or literal).  
- Check dates, numbers, and currencies are localized correctly.  
- Confirm consistency across all sections.

---

## 7. Delivery
When complete, provide:  
1. The bilingual Markdown file (English + Translation + Notes).  
2. An updated `localization_master.csv` with all translations filled in.  
3. Any comments about adaptations you made for cultural sensitivity.

---

✅ This ensures every translation is faithful to the premium emotional tone of the product, while also feeling **native and natural** in the target culture.