Virtual Museum — Flask v4

- Image uploads for artifacts (png/jpg/jpeg/webp) stored under /static/uploads
- FK-safe deletes for artifacts (cleans Purchase & Exhibition_Artifact, removes image file, then Artifact)
- Descriptive complex queries (no Q1/Q2) in queries/complex.sql
- Horizontal, sideways-scroll artifact cards with image centered and details below
- Transactions hidden by default (Admin -> button -> /admin/transactions)

If your Artifact table already has an Image column, the app will use it.
Otherwise it can use Image_URL. It auto-detects which one exists.

## Publishing this repository to GitHub

Follow these steps to publish the project to GitHub from PowerShell. Two options are shown: using the `gh` CLI (recommended if installed) or a manual remote creation via the GitHub website.

1. Initialize git, add files and make the first commit:

```powershell
cd C:\Sem5\DBMS\dbms_mini\virtualmuseum_FIXED
git init
git add .
git commit -m "Initial commit — Virtual Museum"
```

2a. Create a GitHub repository using the `gh` CLI (replace `virtualmuseum` with your name):

```powershell
gh repo create your-username/virtualmuseum --public --source=. --remote=origin --push
```

2b. Or create a repository manually on https://github.com/new, then add the remote and push:

```powershell
git remote add origin https://github.com/your-username/virtualmuseum.git
git branch -M main
git push -u origin main
```

3. After pushing, edit the `LICENSE` file to set your name and optionally change the year.

Notes:
- Replace `your-username` and `virtualmuseum` with your GitHub username and chosen repository name.
- If you want private repo, change `--public` to `--private` in `gh` command or select Private on the GitHub site.
- The repository includes a `.gitignore` to avoid committing virtualenvs and uploaded files (`static/uploads/`). If you prefer to track uploads, remove that line from `.gitignore` before committing.
