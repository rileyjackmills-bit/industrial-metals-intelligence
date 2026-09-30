# 5-minute deployment checklist

You do **not** need Python installed on your computer.

## GitHub
- Create a new public repository: `industrial-metals-intelligence`
- Upload the contents of this folder
- Confirm `app.py` is at the repository root
- Commit

## Streamlit Community Cloud
- Sign in with GitHub
- Create app
- Repository: your new repository
- Branch: `main`
- Main file: `app.py`
- Deploy

No secrets are required.

## If deployment fails
Open the Streamlit deployment log. The most common issue is that the outer folder was uploaded instead of its contents, meaning the app is at `folder-name/app.py` rather than `app.py`.

If that happens, either:
- move the files up one level in GitHub, or
- set the Streamlit main file path to `folder-name/app.py`.
