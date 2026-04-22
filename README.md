# Alfred Confluence search

[![Latest release](https://img.shields.io/github/v/release/Jason-Wheeler/alfred-confluence-plugin?label=latest&color=blue)](https://github.com/Jason-Wheeler/alfred-confluence-plugin/releases/latest)
[![CI](https://github.com/Jason-Wheeler/alfred-confluence-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/Jason-Wheeler/alfred-confluence-plugin/actions/workflows/ci.yml)

An Alfred 5 workflow that searches Atlassian Cloud Confluence, scoped to a configurable set of spaces, and opens the chosen result in your default browser.

Keyword: **`cf`** (e.g. `cf onboarding guide`).

## Install

1. Download **[`ConfluenceSearch.alfredworkflow`](https://github.com/Jason-Wheeler/alfred-confluence-plugin/releases/latest)** from the latest release.
2. Double-click the downloaded file — Alfred opens it and offers to import.
3. Click **Import**.

> Requires Alfred 5 with the Powerpack and macOS (system Python 3 is used — no extra dependencies needed on your machine; the library is bundled inside the workflow).

## Configure

1. Generate an Atlassian API token at <https://id.atlassian.com/manage-profile/security/api-tokens>.
2. In Alfred Preferences → Workflows → **Confluence Search**, click the `[x]` icon top-right to open the configuration sheet.
3. Fill in:
   - **Confluence base URL** — e.g. `https://yourcompany.atlassian.net` (no trailing slash).
   - **Atlassian email** — the email on your Atlassian account.
   - **API token** — the token from step 1.
   - **Space keys** — comma-separated, e.g. `DOCS,ENG,HR`. Leave blank to search every space you can see.

## Use

Trigger Alfred and type `cf` followed by a search term. As you type, results narrow by prefix match on the page title.

- `↵` — open the highlighted page in your default browser.
- `⌘↵` — open the page in Confluence's editor.
- `⌘C` — copy the page URL to the clipboard.
- `⌘Y` / long-press `↵` — Quick Look preview.

If there are no title matches, hit `↵` on the fallback result to full-text search Confluence's own search UI.

## Troubleshoot

- In Alfred Preferences → Workflows → Confluence Search, click the **bug** icon at the top right to open the Debug console. Errors from the script appear there.
- **401 Unauthorized** → wrong email or token.
- **403 Forbidden** → the token is valid but the edge/WAF rejected the request shape; usually means the bundled library got replaced with one that doesn't send `Authorization` pre-emptively. Reinstall from the releases page.
- **No results** → your `Space keys` are scoped too tightly; remove them to search all visible spaces.

---

## Develop

The rest of this README is for hacking on the workflow source. Skip if you just want to use it.

The single file to edit is [`confluence_search.py`](confluence_search.py). Dependencies (the `alfred-pyworkflow` library) are bundled under `lib/` so the workflow is self-contained — macOS's system `/usr/bin/python3` is enough, no virtualenv.

### Local setup

Clone the repo somewhere, install the library into `lib/`, and symlink into Alfred's workflows folder so changes you make are live:

```sh
git clone https://github.com/Jason-Wheeler/alfred-confluence-plugin ~/Code/alfred-confluence-plugin
cd ~/Code/alfred-confluence-plugin
/usr/bin/python3 -m pip install --target=lib --upgrade alfred-pyworkflow
ln -s "$PWD" \
      "$HOME/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows/user.workflow.confluence-search"
```

(If your Alfred prefs sync to Dropbox/iCloud, use that path instead — e.g. `~/Library/CloudStorage/Dropbox/Alfred/Alfred.alfredpreferences/workflows/…`.)

Relaunch Alfred and the workflow shows up as **Confluence Search**.

### Branch workflow

`main` is protected: every change lands via a PR with CI green.

```sh
git checkout -b fix/descriptive-branch-name
# edit, test in Alfred (the symlink keeps it live)
git add -p && git commit -m "Short why-focused message"
git push -u origin HEAD
gh pr create --fill
gh pr merge --squash --delete-branch
```

### Cutting a release

Tag it — CI does the rest:

```sh
git tag -a v0.2.0 -m "Short release notes"
git push origin v0.2.0
```

The `.github/workflows/release.yml` job builds `ConfluenceSearch.alfredworkflow` and publishes it to a new GitHub release with auto-generated notes. The link on this README's **Install** section then points at the new release automatically.

### Upgrade the bundled library

```sh
rm -rf lib/workflow lib/Alfred_PyWorkflow-*.dist-info
/usr/bin/python3 -m pip install --target=lib --upgrade alfred-pyworkflow
```

### Run locally without Alfred

Useful for debugging HTTP errors — Alfred swallows stderr by default.

```sh
CONFLUENCE_BASE_URL='https://yourcompany.atlassian.net' \
CONFLUENCE_EMAIL='you@example.com' \
CONFLUENCE_API_TOKEN='<token>' \
CONFLUENCE_SPACE_KEYS='DOCS' \
PYTHONPATH=./lib /usr/bin/python3 ./confluence_search.py 'onboarding' | python3 -m json.tool
```

## Why `alfred-pyworkflow` instead of `alfred-workflow`?

The original `alfred-workflow` library (the one the [ReadTheDocs site](https://alfred-workflow.readthedocs.io/) documents) imports `cPickle` unconditionally and does not run on Python 3. [`alfred-pyworkflow`](https://pypi.org/project/alfred-pyworkflow/) is a maintained Python 3 fork with the same public API, so the same docs apply.

## Credits

Content-type icons (`assets/content-type-*.png`, `assets/confluence-icon.png`, `assets/search-for.png`) and the workflow icon are adapted from [skleinei/alfred-confluence](https://github.com/skleinei/alfred-confluence), also MIT-licensed.
