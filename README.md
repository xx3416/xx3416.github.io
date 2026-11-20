# Gang Wang — personal homepage

Static single-page site for **https://xx3416.github.io/**, styled after the
typography of [gangw.cs.illinois.edu](https://gangw.cs.illinois.edu/) but
relaid out as a single centred column.

No build step is required: GitHub Pages serves `index.html` straight from the
repository root.

## Layout

| Area | Contents |
| --- | --- |
| Navbar | Name + affiliation, in-page anchors (Home, About, Publications, Press, Students, Activities, Datasets, News) |
| Header | Portrait, name, role, academic-leave status |
| Body | About, publications (2011 → 2027), press coverage, students, professional service, datasets & tools, news |

## What was removed

The page carries no way to contact or trace the person it describes:

* e-mail address, UIUC office address and phone number
* CV (both the navbar link, the section and `CV.pdf`)
* Google Scholar, DBLP, Twitter and GitHub profile links
* the sidebar's CLASS teaching list, news column and sponsor logos

The remaining external links are the publication PDFs and code repositories
that the reference site itself publishes — see `STRIP_REFERENCE_LINKS` below.

## Adaptations vs. the reference site

* **Portrait replaced** with a neutral `GW` initials avatar (`image/avatar.svg`).
* **University wordmark replaced** with plain `ByteDance` text in the navbar.
* **Bio rewritten** to state that Gang Wang is a Research Scientist at ByteDance
  and has been on academic leave from UIUC since June 2025.
* **Single column** — the reference's 3/9 sidebar split is gone; the page is
  one centred column with the portrait in a header block.
* **Single page** — the reference's `publication.html`, `press.html`,
  `students.html`, `activity.html` and `data.html` content is merged into
  in-page sections, and the navbar links are anchors.
* All 62 news items live in the "News" section of the body.

## Layout files

```
index.html          the page
css/bootstrap.css   Bootstrap 3.3.4 (from the reference site)
css/non-responsive.css
css/site.css        local overrides
css/*.js            jQuery + Bootstrap (navbar toggle)
image/avatar.svg    portrait placeholder
fonts/              pushpin icon
```

## Regenerating `index.html`

`_build/build_site.py` regenerates `index.html` from the reference snapshots in
`_build/src/`:

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
`https://xx3416.github.io/`. Enable Pages with **Settings → Pages → Source:
Deploy from a branch → `main` / root (`/`)**.

Push over SSH using the dedicated key configured on this machine:

```bash
git remote add origin git@github-xx3416:xx3416/xx3416.github.io.git
git push -u origin main
```

The SSH alias `github-xx3416` is defined in `~/.ssh/config` and points at
`ssh.github.com:443` (port 22 is blocked on this network) with the key
`~/.ssh/id_ed25519_xx3416`.
