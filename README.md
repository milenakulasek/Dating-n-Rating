# Dating Candidate Ranker (Private)

A Streamlit app (in English) for ranking people you are dating based on your own criteria.

## Features
- Add people with notes
- Configure point tiles (label, category, points)
- Add points by clicking tiles (absolute values, not 1-10 scale)
- Auto-calculated total score from category points
- Sortable ranking table
- Notes and red flags
- Delete selected entry
- Local data backup (download/upload `data.xlsx`)

## Run locally
1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start app:
   - `streamlit run app.py`

## Privacy guidance
Your data is stored in local Excel file `data.xlsx`.

To keep data private:
- Run the app on your own machine only.
- Keep `.streamlit/secrets.toml` out of git (already in `.gitignore`).
- Keep `data.xlsx` out of git (already in `.gitignore`).
- If deploying online, use a private database and access control (login, allowlist, VPN, or private hosting).

## Deployment note
If you deploy on Streamlit Community Cloud, the app URL is public by default unless you add strong access control and avoid storing sensitive data there.
