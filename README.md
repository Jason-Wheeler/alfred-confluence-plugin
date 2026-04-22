# Alfred Confluence search

An Alfred 5 workflow that searches Atlassian Cloud Confluence, scoped to a configurable set of spaces, and opens the chosen result in your default browser.

Keyword: **`cf`** (e.g. `cf onboarding guide`).

## Install

This repo *is* the Alfred workflow — `info.plist` and the script live alongside each other. To make Alfred pick it up, symlink the repo into Alfred's `workflows` folder:

```sh
ln -s "$HOME/Code/alfred-confluence-plugin" \
      "$HOME/Library/CloudStorage/Dropbox/Alfred/Alfred.alfredpreferences/workflows/user.workflow.confluence-search"
```

Quit and relaunch Alfred. The workflow appears in Alfred Preferences → Workflows as **Confluence Search**.

> **Sync caveat:** the real code lives outside Alfred's Dropbox-synced folder. Alfred will work on this Mac, but if you want the workflow on another machine too, either move the repo into Dropbox or export a `.alfredworkflow` bundle.

## Configure

1. Generate an Atlassian API token at <https://id.atlassian.com/manage-profile/security/api-tokens>.
2. In Alfred Preferences → Workflows → **Confluence Search**, click the `[x]` icon top-right to open the configuration sheet.
3. Fill in:
   - **Confluence base URL** — e.g. `https://ef.atlassian.net` (no trailing slash).
   - **Atlassian email** — the email on your Atlassian account.
   - **API token** — the token from step 1.
   - **Space keys** — comma-separated, e.g. `DOCS,ENG,HR`. Leave blank to search every space you can see.

## Use

Trigger Alfred, type `cf` followed by a search term. Arrow through results; Return opens the highlighted page in your default browser.

## Develop

The single file you edit is [`confluence_search.py`](confluence_search.py). Dependencies (the `alfred-pyworkflow` library) are bundled under [`lib/`](lib/) so the workflow is self-contained — macOS's system `/usr/bin/python3` is enough, no virtualenv.

### Workflow

Every change goes on a short-lived feature branch and lands in `main` via a self-reviewed PR:

```sh
git checkout -b fix/ordering-by-title
# edit, test in Alfred (the repo is symlinked so changes are live)
git add -p && git commit -m "Sort results by title match rank"
git push -u origin HEAD
gh pr create --fill            # or --web to open in browser
gh pr merge --squash --delete-branch
```

`main` is always in a state where Alfred can load the workflow cleanly. The Dropbox-synced symlink means whatever is on disk in `main` is what Alfred runs.

### Upgrade the bundled library

```sh
rm -rf lib/workflow lib/Alfred_PyWorkflow-*.dist-info
/usr/bin/python3 -m pip install --target=lib --upgrade alfred-pyworkflow
```

### Run locally without Alfred

Useful for debugging HTTP errors — Alfred swallows stderr by default.

```sh
CONFLUENCE_BASE_URL='https://ef.atlassian.net' \
CONFLUENCE_EMAIL='jason.wheeler@ef.com' \
CONFLUENCE_API_TOKEN='<token>' \
CONFLUENCE_SPACE_KEYS='DOCS' \
PYTHONPATH=./lib /usr/bin/python3 ./confluence_search.py 'onboarding' | python3 -m json.tool
```

## Troubleshoot

- In Alfred, open the workflow and click **View → Debug** to see stderr output from the script.
- 401 Unauthorized → wrong email or token.
- Empty results → check the `Space keys` field; if scoped to a space the term isn't in, you'll see zero hits.
- `ModuleNotFoundError: No module named 'workflow'` → the `lib/` directory is missing the bundled library; re-run the install command above.

## Why `alfred-pyworkflow` instead of `alfred-workflow`?

The original `alfred-workflow` library (the one the [ReadTheDocs site](https://alfred-workflow.readthedocs.io/) documents) imports `cPickle` unconditionally and does not run on Python 3. [`alfred-pyworkflow`](https://pypi.org/project/alfred-pyworkflow/) is a maintained Python 3 fork with the same public API, so the same docs apply.
