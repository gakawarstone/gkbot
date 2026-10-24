# Feed source matching and item policy

The feed dispatcher uses the registry for every source. It has no legacy URL
map and inherits only the shared generic web renderer. Source factories own
matching and processing; adding a source requires its factory and composition
entry, without changing registry internals or a view inheritance list.

## Matching

`processors.matching.matches_source_url` parses the URL before comparing its
scheme, hostname, and optional path. Hostname and scheme matching is case
insensitive; a trailing hostname dot and the scheme's default port are accepted.
Userinfo, whitespace, malformed authorities, nondefault ports, and unsupported
schemes do not select a source. Parsing failures return a registry miss rather
than entering the processor's execution boundary.

Source declarations are kept in their own processor modules:

| Identity | Hostnames or hostname family | Scheme/path |
| --- | --- | --- |
| `stories` | Hostname begins with `stor` | HTTPS |
| `kinogo` | Hostname begins with `kinogo` | HTTPS |
| `spoti` | `open.spotify.com` | HTTPS |
| `vk` | `vk.com` | HTTPS |
| `youtube` | `www.youtube.com` | HTTPS |
| `telegram` | `t.me` | HTTPS |
| `reddit` | `www.reddit.com` | HTTPS |
| `rezka` | `hdrezka.me` | HTTPS |
| `shiki` | `shikimori.one`, `shikimori.me`, `shikimori.org` | HTTPS |
| `twitch` | `www.twitch.tv` | HTTPS |
| `tiktok` | `www.tiktok.com` | HTTPS |
| `pornhub` | `www.pornhub.com`, `de.pornhub.org`, `pornhub.org` | HTTPS |
| `porno365` | `porno365.broker` | HTTP |
| `discours` | `discours.io` | HTTPS |
| `instagram` | `instagram.com`, `www.instagram.com` | HTTPS |
| `hltv` | `www.hltv.org` | HTTPS |
| `sasflix` | `sasflix.ru` | HTTPS |
| `matreshka` | `matreshka.tv` | HTTPS, path starts with `/video/` |

Stories and Kinogo previously matched unspecified CDN and mirror hostnames.
Their hostname families remain compatible because the repository contains no
enumeration of those hosts. These two declarations can match longer hostnames;
they are not domain ownership checks. Exact hostname lists can replace the
families in those source modules when available. All other sources use exact
hostnames. No source is selected from a URL appearing in a path, query, fragment,
or userinfo. The table documents the declarations; it is not a second dispatch
map used by code.

## Content policy

`modules.feed.handlers.policy.FeedSourcePolicy` takes a registry and a frozen
set of rejected `source_id` values. `allows(item)` resolves the item using that
registry and compares its identity with the rejected set. Aliases share one
policy identity. Matching errors propagate; policy evaluation never runs a
processor or fetches metadata.

Both `ShowFeedItemsHandler` and `ItemEventHandler` pass the shared
`_source_policy.allows` predicate to `GkfeedItemsPicker.get_next_item`. The picker
rejects an item before saving it to its per-login pocket, then continues to the
next eligible item. Sorting, pocket exhaustion/reset, and the empty-feed response
are unchanged. The rejected identities are supplied by the common handler's
`_rejected_source_ids` composition setting.

The default rejected set is empty. This preserves every current subscription;
no new production content exclusions are inferred from source names. Unknown
sources are allowed and use generic Open Graph rendering. For example, a policy
constructed with `frozenset({"pornhub"})` rejects each registered Pornhub alias
without rejecting an unrelated URL mentioning `pornhub.org` in its query.

The HTTP API and its cache return transport records independently of policy.
The decoder's existing omission of empty-link records remains unchanged, including
its sparse-record behavior. Direct item lookup is also independent of policy.

## Failure behavior and tests

Registered sources call `_run_processor` with their stable identity. Generic
rendering uses the same execution boundary. The existing recoverable-error
allowlist sends the plain link once and logs bounded metadata; unexpected errors,
cancellation, matcher errors, and fallback-sender errors propagate. See the
[exception contract](feed-processor-exceptions.md).

`test_feed_source_policy.py` covers accepted, rejected and unknown items, every
registered source and alias, URL authority boundaries, both active entry points,
pocket order and login isolation. Existing source regression tests cover media,
keyboard payloads, generic rendering and failure fallback. `test_gkfeed_api.py`
checks that list/cache and direct-item transport preserve source records.

The integration base is task12 head
`96d9b9c5b436f47d2822e1929e0397423c512ebd`, which includes task11's
`9e4fe280867b77a413d3a334b808b1f1ee0f4656`, registry
`1cda1a9cd415b72274d2ec3e96912961ea27410f`, and exception prerequisite
`6123f94fbfd2c169df27c336becb853b46ea1fd8`.

Validation on 2026-10-24: `make test` passed with 541 passed and 13 skipped.
File-scoped `make lint` passed Ruff, typos, mypy and pyright for the dispatcher,
entry-point handlers, policy, all processor modules and affected tests. Three
existing invalid-handler checks retain `ValueError` with local Ruff exceptions;
the existing TaskGroup unwrap also retains its behavior. No repository-wide lint
cleanup is included.
