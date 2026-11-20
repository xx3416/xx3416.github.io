# Gang Wang — personal homepage

Static single-page site for **https://xx3416.github.io/**, styled after the
layout of [gangw.cs.illinois.edu](https://gangw.cs.illinois.edu/).

No build step is required: GitHub Pages serves `index.html` straight from the
repository root.

## Layout

| Area | Contents |
| --- | --- |
| Navbar | Name + affiliation, in-page anchors (Home, Publications, Press, Students, Activities, Datasets, CV) |
| Sidebar | Avatar, contact, scholar/DBLP/Twitter/GitHub links, CLASS list, latest news, sponsor logos |
| Main column | Bio, publications (2011 → 2027), press coverage, students, professional service, datasets & tools, archived news, CV |

## Adaptations vs. the reference site

* **Email removed** — the contact block lists the office address and phone only.
* **Portrait replaced** with a neutral `GW` initials avatar (`image/avatar.svg`).
* **University wordmark replaced** with plain `ByteDance` text in the navbar.
* **Bio rewritten** to state that Gang Wang is a Research Scientist at ByteDance
  and has been on academic leave from UIUC since June 2025.
* **Single page** — the reference's `publication.html`, `press.html`,
  `students.html`, `activity.html` and `data.html` content is merged into
  in-page sections, and the navbar links are anchors.
* **News split** — the 12 most recent items sit in the sidebar, the remaining 50
  are in the "Archived News" section at the bottom.
* Paper/asset links point back at `gangw.cs.illinois.edu`, since the PDFs and
  datasets themselves are not hosted here.

## Layout files

```
index.html          the page
css/bootstrap.css   Bootstrap 3.3.4 (from the reference site)
css/non-responsive.css
css/site.css        local overrides
css/*.js            jQuery + Bootstrap (navbar toggle)
image/              sponsor logos + avatar
fonts/              pushpin icon
CV.pdf              curriculum vitae
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
