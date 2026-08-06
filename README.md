# DingoNav — moved

The source for DingoNav now lives in the **[dingodirt monorepo](https://github.com/grantpaisley/dingodirt)**
at [`apps/nav`](https://github.com/grantpaisley/dingodirt/tree/main/apps/nav),
alongside Plan, Studio and the dingodirt.com site. Issues and pull requests
belong there. (This README's original contents are preserved verbatim at
`apps/nav/README.md`, and in this repo's git history.)

This repo is kept alive for one reason: the URL below must keep serving.

## https://grantpaisley.github.io/DingoNav/

Installed PWAs and every pack share link already in the wild point at it — the
daemon hardcodes it as the share-link default — so it is not going away.

[`.github/workflows/mirror-nav.yml`](.github/workflows/mirror-nav.yml) rebuilds
that site from the monorepo every six hours, and on demand via
*Actions → Mirror Nav from the monorepo → Run workflow*. It checks the monorepo
out — no credential needed, it is public — runs the same
`tools/assemble-app.sh` the monorepo's own deploy uses, and publishes with this
repo's own `GITHUB_TOKEN`. No cross-repo token exists anywhere in the chain.

So a change to `apps/nav` reaches this URL within six hours, or immediately if
you run the workflow by hand.

The same build is also served at
[grantpaisley.github.io/dingodirt/nav/](https://grantpaisley.github.io/dingodirt/nav/).

## The old source

Everything from before the migration is still in this repo's git history, and
the branches are untouched. Nothing was deleted — development just happens
elsewhere now.
