# Step-by-step: Put the pet on your GitHub profile README (testing)

Do this in the repo that shows on your profile (the one named **exactly** your GitHub username, e.g. `jane` for user `jane`).

---

## Step 1: Push the action code (if you haven’t)

Make sure the `gh-tamagotchi` repo (this one) is pushed to GitHub with:

- `.github/actions/generate-pet/action.yml`
- `scripts/generate_pet.py`
- Rest of the project (so the action can install from it)

If you’re testing from a **fork**, push your fork. Note the **owner** of that repo (e.g. your username or org). You’ll use it in Step 3 as `OWNER`.

---

## Step 2: Open your profile repo

- Go to **https://github.com/YOUR_USERNAME/YOUR_USERNAME** (replace `YOUR_USERNAME` with your GitHub username).
- If it doesn’t exist: **New repository** → name it **exactly** your username → add a `README.md` → Create.

---

## Step 3: Add the workflow

In that profile repo:

1. Click **Add file** → **Create new file**.
2. In the name box type: **`.github/workflows/pet.yml`** (including the leading dot and the path).
3. Paste this **exactly** (then replace `OWNER` in the `uses` line):

```yaml
name: Update GitHub Tamagotchi Pet

on:
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  pet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: OWNER/gh-tamagotchi/.github/actions/generate-pet@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

4. Replace **`OWNER`** with the owner of the `gh-tamagotchi` repo:
   - This repo is under your user → use your username.
   - You use a fork → use your username (or the org that owns the fork).
   - Example: if the repo is `https://github.com/hp/gh-tamagotchi`, use `hp` →  
     `uses: hp/gh-tamagotchi/.github/actions/generate-pet@main`
5. Click **Commit changes** → **Commit directly to the default branch**.

---

## Step 4: Add the pet to your README

Still in the same profile repo:

1. Open **README.md**.
2. Where you want the pet to appear, add this line (you can put it at the top):

```markdown
![GitHub Tamagotchi](pet.svg)
```

3. Commit the change.

(The first time you run the workflow, it will create `pet.svg`. Until then, the image may 404; that’s normal.)

---

## Step 5: Run the workflow once

1. In your profile repo, open the **Actions** tab.
2. In the left sidebar, click **“Update GitHub Tamagotchi Pet”**.
3. Click **“Run workflow”** (dropdown on the right) → **“Run workflow”** again.
4. Wait for the run to finish (green checkmark). It will commit `pet.svg` and `.pet-state.json` to your repo.

---

## Step 6: Check your profile

- Go to **https://github.com/YOUR_USERNAME** (your profile page).
- Your README should show the pet image. If it doesn’t, refresh or wait a few seconds for the commit to be visible.

---

## Quick checklist

| Step | What to do |
|------|------------|
| 1 | Push `gh-tamagotchi` (with the action) to GitHub; note `OWNER`. |
| 2 | Open repo `YOUR_USERNAME/YOUR_USERNAME` (create it if needed). |
| 3 | Create `.github/workflows/pet.yml` and set `uses: OWNER/gh-tamagotchi/.github/actions/generate-pet@main`. |
| 4 | In `README.md` add: `![GitHub Tamagotchi](pet.svg)`. |
| 5 | Actions → “Update GitHub Tamagotchi Pet” → Run workflow. |
| 6 | Open your profile and confirm the pet shows. |

---

## If something fails

- **“Unable to resolve action”**  
  Fix the `uses` line: `OWNER` must be the GitHub user/org that owns the `gh-tamagotchi` repo (e.g. `hp` if the repo is `hp/gh-tamagotchi`).

- **Pet image broken (404)**  
  Run the workflow once (Step 5). The image works only after the first successful run that creates `pet.svg`.

- **Workflow fails on “Generate pet”**  
  Open the failed run → click the “Generate pet” step and read the log. Common causes: wrong Python/deps (action repo must have `requirements.txt` and script at `scripts/generate_pet.py`) or GitHub API rate limit (wait a bit and re-run).
