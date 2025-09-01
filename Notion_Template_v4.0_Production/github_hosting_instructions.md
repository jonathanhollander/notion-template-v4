# GitHub Hosting Instructions for Notion Template Assets

This document outlines the steps to host your generated Notion template assets (icons and covers) on GitHub Pages for easy integration.

**Prerequisites:**

*   A GitHub account.
*   `git` installed and configured on your local machine.
*   Your generated assets located in the `assets/` directory of your Notion project.

---

## Step 1: Create a New, Empty GitHub Repository

1.  Go to [https://github.com/new](https://github.com/new) in your web browser.
2.  **Repository Name:** Choose a descriptive name (e.g., `notion-template-assets`, `estate-planning-concierge-assets`).
3.  **Visibility:** Select `Public` (required for GitHub Pages to serve content publicly).
4.  **Initialization:** **IMPORTANT:** Do NOT initialize the repository with a README, .gitignore, or license. Leave it completely empty.
5.  Click the "Create repository" button.

---

## Step 2: Prepare and Push Your Assets to the New Repository

These commands should be run in your local terminal. Ensure you are in the root directory of your Notion project (`/Users/jonathanhollander/AI Code/Notion Template/Notion_Template_v4.0_Production/`).

1.  **Create a temporary directory for the assets repository:**
    This keeps the assets separate from your main Notion project's Git history (if it has one).

    ```bash
    mkdir notion_assets_repo
    ```

2.  **Copy the generated assets into this new directory:**

    ```bash
    cp -R assets/covers_* notion_assets_repo/
    cp -R assets/icons_* notion_assets_repo/
    ```

3.  **Navigate into the new assets repository directory:**

    ```bash
    cd notion_assets_repo
    ```

4.  **Initialize a new Git repository in this directory:**

    ```bash
    git init
    ```

5.  **Add all the copied asset files to the staging area:**

    ```bash
    git add .
    ```

6.  **Commit the assets:**

    ```bash
    git commit -m "Add all generated Notion template assets (icons and covers for all themes)"
    ```

7.  **Add the remote GitHub repository:**
    **IMPORTANT:** Replace `YOUR_USERNAME` with your GitHub username and `YOUR_REPOSITORY_NAME` with the name of the repository you created in Step 1.

    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
    ```

8.  **Push the committed changes to GitHub:**
    **IMPORTANT:** Replace `main` with `master` if your GitHub repository's default branch is `master`.

    ```bash
    git push -u origin main
    ```

---

## Step 3: Enable GitHub Pages for Your Repository

This step tells GitHub to serve your repository's content as a website.

1.  On your GitHub repository page, click on **"Settings"** (usually near the top right).
2.  In the left sidebar, click on **"Pages"**.
3.  Under "Build and deployment," for "Source," select **"Deploy from a branch."**
4.  For "Branch," choose the branch where your assets are located (usually `main` or `master`).
5.  For "Folder," select `/ (root)`. This ensures that the `assets/` folder (and its contents) within your repository will be accessible via the GitHub Pages URL.
6.  Click **"Save."**

---

## Step 4: Get Your GitHub Pages URL

After saving, GitHub Pages will build your site. This usually takes a few moments.

*   Refresh the "Pages" section in your repository settings.
*   You will see a message like: `Your site is published at https://YOUR_USERNAME.github.io/YOUR_REPOSITORY_NAME/`.
*   This URL (`https://YOUR_USERNAME.github.io/YOUR_REPOSITORY_NAME/`) is your **base URL** for the assets.

---

## Step 5: Update Your `deploy.py` Script (Manual Action)

You will need to manually modify your `deploy.py` script to use these new asset URLs.

1.  **Define the `ASSET_BASE_URL`:**
    Add this line near the top of your `deploy.py` script, replacing the placeholder with your actual GitHub Pages base URL from Step 4.

    ```python
    ASSET_BASE_URL = "https://YOUR_USERNAME.github.io/YOUR_REPOSITORY_NAME/"
    ```

2.  **Modify `get_asset_icon` and `get_asset_cover` functions:**
    Locate these functions in your `deploy.py` script. You'll need to adjust them to construct the full HTTP(S) URLs using the `ASSET_BASE_URL`.

    **Example modification (conceptual):**

    ```python
    def get_asset_icon(asset_name: str, theme: str = "default", custom_themes_db_id: str = None) -> Optional[Dict]:
        # ... (existing logic to determine asset_name and theme, ensuring asset_name is like "page_title_icon.png") ...

        # Construct the full URL for the icon
        icon_url = f"{ASSET_BASE_URL}assets/icons_{theme}/{asset_name}"
        return {"type": "external", "external": {"url": icon_url}}

    def get_asset_cover(asset_name: str, theme: str = "default", custom_themes_db_id: str = None) -> Optional[Dict]:
        # ... (existing logic to determine asset_name and theme, ensuring asset_name is like "page_title_cover.png") ...

        # Construct the full URL for the cover
        cover_url = f"{ASSET_BASE_URL}assets/covers_{theme}/{asset_name}"
        return {"type": "external", "external": {"url": cover_url}}
    ```

    *Ensure that `asset_name` passed to these functions is the sanitized filename (e.g., `admin_release_notes_icon.png`), not the original page title or SVG filename.*

---

**Important Considerations:**

*   **File Paths:** Ensure the paths within your `assets/` directory (e.g., `assets/icons_default/`) match the structure you push to GitHub.
*   **Case Sensitivity:** GitHub Pages can be case-sensitive, especially on Windows. Ensure your filenames and paths match exactly (e.g., `icons_default` vs `Icons_Default`).
*   **Caching:** Browsers and Notion might cache old asset URLs. If you update assets, you might need to clear your browser cache or Notion's cache to see the changes immediately.
