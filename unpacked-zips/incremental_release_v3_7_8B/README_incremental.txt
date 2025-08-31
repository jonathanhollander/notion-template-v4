INCREMENTAL RELEASE v3.7.8B
---------------------------
This package completes the remaining fixes on top of v3.7.8 and v3.7.8A with **API-safe**, idempotent content.

FILES
 • 10_personalization_settings.yaml — Admin Settings and Acceptance patch for Estate Complexity selection.
 • 11_executor_task_profiles.yaml — Simple/Moderate/Complex executor task packs (choose one; delete others).
 • 12_letters_content_patch.yaml — Realistic, ready-to-adapt letters (body + disclaimer).
 • 13_hub_ui_embeds.yaml — Hub progress/embed guidance with idempotent markers.
 • 14_assets_standardization.yaml — Admin asset checklist for consistent visuals.
 • 15_mode_guidance.yaml — Beginner/Advanced guidance pages (per Hub).

HOW TO APPLY
1) Copy these YAML files into your split_yaml/ directory (keep existing files).
2) Preview:  python deploy/deploy_v3_5.py --dir split_yaml --dry-run
3) Deploy:   python deploy/deploy_v3_5.py --dir split_yaml --deploy
4) Complete Admin steps, confirm Rollout Summary, and delete Admin pages before sharing.

NOTES
- No script changes are required for these patches.
- All additions use markers or are safe to delete post-setup.
- Nothing new is exposed to end users once Admin pages are removed.
