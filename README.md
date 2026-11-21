# Gang Wang — personal homepage

Static single-page site for **https://xx3416.github.io/gangwang/**, styled
after the typography of
[gangw.cs.illinois.edu](https://gangw.cs.illinois.edu/) but relaid out as a
single centred column.

No build step is required: GitHub Pages serves `gangwang/index.html` straight
from the repository.

## Layout

| Area | Contents |
| --- | --- |
| Navbar | Name + affiliation, in-page anchors (Home, About, Publications, Press, Activities, Datasets, News) |
| Header | Portrait, name, role, academic-leave status |
| Body | About, publications (2011 → 2025), press coverage, professional service, datasets & tools, news |

## The address

The site has one address, **`https://xx3416.github.io/gangwang/`**:

| URL | File |
| --- | --- |
| `https://xx3416.github.io/gangwang/` | `gangwang/index.html` — the page |
| `https://xx3416.github.io/` | `index.html` — redirect stub |

`index.html` at the root only redirects: a meta refresh plus
`window.location.replace`, which carries the fragment of the old URL over, so
`https://xx3416.github.io/#publications` still lands on the publications
section. `gangwang/index.html` carries `<link rel="canonical">` pointing at
itself, so search engines index the `/gangwang/` address.

The page's asset paths are absolute (`/css/...`, `/fonts/...`, `/image/...`),
because from `/gangwang/` a relative `css/...` would resolve to
`/gangwang/css/...`.

## What was removed

The page carries no way to contact or trace the person it describes:

* e-mail address, UIUC office address and phone number
* CV (both the navbar link, the section and `CV.pdf`)
* Google Scholar, DBLP, Twitter and GitHub profile links
* the sidebar's CLASS teaching list, news column and sponsor logos
* the students section and its navigation entry
* the 2026 and 2027 publication entries (see `EXCLUDE_YEARS` below)
* the `Code` and `Press` quick-link buttons on the publication entries
  (see `REMOVE_QUICKLINKS` below)
* the 11 most recent news entries, from "28 Sep 2026" to "7 Oct 2025"
  (see `NEWS_SKIP` below)

The paper and dataset links that used to point back at the reference site
are now rendered as inert chips — the page contains no path back to it.

## Adaptations vs. the reference site

* **Portrait replaced** with a neutral `GW` initials avatar (`image/avatar.svg`).
* **University wordmark replaced** with plain `ByteDance` text in the navbar.
* **Bio rewritten** to state that Gang Wang is a Research Scientist at ByteDance
  and has been on academic leave from UIUC since June 2025.
* **Single column** — the reference's 3/9 sidebar split is gone; the page is
  one centred column with the portrait in a header block.
* **Single page** — the reference's `publication.html`, `press.html`,
  `activity.html` and `data.html` content is merged into
  in-page sections, and the navbar links are anchors.
* The 51 news items from 17 Aug 2025 back to 26 May 2022 live in the "News" section.

## Layout files

```
index.html          redirect to /gangwang/
gangwang/index.html the page
css/bootstrap.css   Bootstrap 3.3.4 (from the reference site)
css/non-responsive.css
css/site.css        local overrides
css/*.js            jQuery + Bootstrap (navbar toggle)
image/avatar.svg    portrait placeholder
fonts/              pushpin icon
```

## Regenerating the page

`_build/build_site.py` regenerates `gangwang/index.html` and the root
redirect from the reference snapshots in `_build/src/`:

```bash
cd _build
python build_site.py
```

The script rewrites relative links, strips HTML comments, and rebalances
`<p>`/`<div>`/`<em>`/`<a>` markup that the source pages leave unbalanced.

Set `STRIP_REFERENCE_LINKS = True` at the top of that script to render the
paper/dataset links back to `gangw.cs.illinois.edu` as plain text, leaving the
page with no path back to the reference site at all.

## Publishing

The repository should be named `xx3416.github.io` so GitHub Pages serves it at
`https://xx3416.github.io/gangwang/`. Enable Pages with **Settings → Pages →
Source: Deploy from a branch → `main` / root (`/`)**.

Push over SSH using the dedicated key configured on this machine:

```bash
git remote add origin git@github-xx3416:xx3416/xx3416.github.io.git
git push -u origin main
```

The SSH alias `github-xx3416` is defined in `~/.ssh/config` and points at
`ssh.github.com:443` (port 22 is blocked on this network) with the key
`~/.ssh/id_ed25519_xx3416`.
