#!/usr/bin/env python3
# encoding: utf-8

"""Alfred Script Filter: search Confluence Cloud and emit clickable results."""

import base64
import os
import sys
import urllib.parse

from workflow import ICON_WARNING, Workflow, web

HELP_URL = 'https://id.atlassian.com/manage-profile/security/api-tokens'
CONTENT_TYPES = ('page', 'blogpost')

ICON_PAGE = './assets/content-type-page.png'
ICON_BLOGPOST = './assets/content-type-blogpost.png'
ICON_ATTACHMENT = './assets/content-type-attachment.png'
ICON_SEARCH_FOR = './assets/search-for.png'

EXPAND = ','.join([
    'content.space',
    'content.metadata.properties.emoji_title_published',
    'content.history.lastUpdated',
])


def basic_auth_header(email, token):
    # Send auth pre-emptively. urllib's HTTPBasicAuthHandler waits for a 401
    # challenge before retrying with creds, but Confluence Cloud returns 403
    # on unauthenticated requests, so the retry never happens.
    raw = '{}:{}'.format(email, token).encode('utf-8')
    return 'Basic ' + base64.b64encode(raw).decode('ascii')


def build_cql(query, space_keys):
    q = query.replace('\\', '\\\\').replace('"', '\\"')
    # CQL's `~` is word-level, so "web pub" wouldn't match "Website publishing".
    # Append `*` to every word for prefix matching — mirrors Confluence's own
    # incremental search behavior.
    words = [w if w.endswith('*') else w + '*' for w in q.split()]
    q_wildcard = ' '.join(words) if words else q
    parts = ['title ~ "{}"'.format(q_wildcard)]
    if space_keys:
        parts.append('space.key in ({})'.format(
            ', '.join('"{}"'.format(k) for k in space_keys)))
    parts.append('type in ({})'.format(
        ', '.join('"{}"'.format(t) for t in CONTENT_TYPES)))
    return ' AND '.join(parts) + ' ORDER BY lastmodified DESC'


def icon_for(content_type):
    if content_type == 'blogpost':
        return ICON_BLOGPOST
    if content_type == 'attachment':
        return ICON_ATTACHMENT
    return ICON_PAGE


def emoji_prefix(content):
    # Confluence stores a page's emoji as a hex unicode codepoint under
    # metadata.properties.emoji-title-published (e.g. '1F389' → 🎉).
    props = (content.get('metadata') or {}).get('properties') or {}
    emoji = props.get('emoji-title-published') or props.get('emoji_title_published')
    if not emoji:
        return ''
    hex_str = emoji.get('value') if isinstance(emoji, dict) else emoji
    if not hex_str:
        return ''
    try:
        return chr(int(hex_str, 16)) + ' '
    except (ValueError, TypeError):
        return ''


def main(wf):
    query = (wf.args[0] if wf.args else '').strip()

    base_url = os.environ.get('CONFLUENCE_BASE_URL', '').strip().rstrip('/')
    email = os.environ.get('CONFLUENCE_EMAIL', '').strip()
    token = os.environ.get('CONFLUENCE_API_TOKEN', '').strip()
    space_keys = [s.strip() for s in
                  os.environ.get('CONFLUENCE_SPACE_KEYS', '').split(',')
                  if s.strip()]

    if not (base_url and email and token):
        wf.add_item('Workflow not configured',
                    'Set base URL, email, and API token in the workflow settings.',
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    if not query:
        wf.add_item('Type to search Confluence…',
                    'e.g. cf onboarding guide',
                    icon=ICON_SEARCH_FOR)
        wf.send_feedback()
        return 0

    cql = build_cql(query, space_keys)
    r = web.get('{}/wiki/rest/api/search'.format(base_url),
                params={'cql': cql, 'limit': 25, 'expand': EXPAND},
                headers={'Authorization': basic_auth_header(email, token),
                         'Accept': 'application/json'})
    r.raise_for_status()
    data = r.json()

    results = data.get('results', [])
    if not results:
        fallback_url = '{}/wiki/search?text={}'.format(
            base_url, urllib.parse.quote(query))
        wf.add_item('No title matches for \u201c{}\u201d'.format(query),
                    'Hit Enter to full-text search Confluence',
                    arg=fallback_url,
                    valid=True,
                    icon=ICON_SEARCH_FOR)
        wf.send_feedback()
        return 0

    for result in results:
        content = result.get('content') or {}
        page_id = content.get('id', '') or ''
        ctype = content.get('type') or 'page'

        raw_title = content.get('title') or result.get('title') or 'Untitled'
        title = emoji_prefix(content) + raw_title

        space = content.get('space') or {}
        space_name = space.get('name') or (result.get('resultGlobalContainer') or {}).get('title', '')
        modified = result.get('friendlyLastModified', '')
        last_by = (((content.get('history') or {}).get('lastUpdated') or {}).get('by') or {}).get('displayName', '')
        subtitle_parts = [p for p in [space_name, modified, 'by ' + last_by if last_by else ''] if p]
        subtitle = ' · '.join(subtitle_parts) or 'Confluence page'

        rel = result.get('url', '') or ''
        full_url = ('{}{}' if rel.startswith('/wiki') else '{}/wiki{}').format(base_url, rel)

        item = wf.add_item(
            title=title,
            subtitle=subtitle,
            arg=full_url,
            valid=True,
            uid=page_id or full_url,
            icon=icon_for(ctype),
            quicklookurl=full_url,
            copytext=full_url,
            largetext=full_url,
        )

        if ctype in ('page', 'blogpost') and page_id:
            editor_url = '{}/wiki/pages/editpage.action?pageId={}'.format(base_url, page_id)
            item.add_modifier('cmd',
                              subtitle='Open in editor',
                              arg=editor_url,
                              valid=True)

    wf.send_feedback()
    return 0


if __name__ == '__main__':
    wf = Workflow(help_url=HELP_URL)
    sys.exit(wf.run(main))
