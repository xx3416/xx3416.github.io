#!/usr/bin/env python3
"""Assemble the xx3416 personal homepage.

Reads the reference snapshots in ./src (captured from gangw.cs.illinois.edu)
and emits a single-page GitHub Pages site into ../ (the publishable root).

The output keeps the reference layout:
  * Bootstrap 3.3.4 + non-responsive CSS (copied verbatim from the reference)
  * fixed navbar, col-xs-3 sidebar / col-xs-9 main column
  * single Home page: every nav entry is an in-page anchor

Local adaptations:
  * portrait  -> neutral "GW" initials avatar (no third-party photo)
  * Illinois wordmark -> plain "ByteDance" text
  * e-mail    -> removed
  * bio       -> ByteDance research role, academic leave from UIUC since June 2025

Usage:  python build_site.py
"""

import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "src")
REF = "https://gangw.cs.illinois.edu/"

# When True, links back to the reference site (paper PDFs, datasets) are
# rendered as plain text instead of anchors. Flip to True to remove every
# path from this page back to gangw.cs.illinois.edu.
STRIP_REFERENCE_LINKS = True

# Publication years to leave out of the list entirely.
EXCLUDE_YEARS = {"2026", "2027"}

# Quick-link buttons to drop from the publication entries.
REMOVE_QUICKLINKS = {"Code", "Press"}
QUICKLINK = re.compile(
    r'<a[^>]*class="[^"]*btn-xs[^"]*"[^>]*>\s*(?:%s)\s*</a>' % "|".join(REMOVE_QUICKLINKS),
    re.I)

# The most recent news entries are not listed on the page: everything from
# "28 Sep 2026" down to and including "7 Oct 2025" (Revelio) is dropped, so
# the oldest entry shown is "17 Aug 2025".
NEWS_SKIP = 11

# The reference snapshot is kept in the repository so the page can be rebuilt
# offline, which means it must not carry the contact details of the person it
# describes. These are stripped from the snapshot on every build and the
# cleaned copy is written back to disk.
SNAPSHOT_CONTACT = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[email removed]"),
    (re.compile(r"Phone:\s*[\d\-\(\)\. ]{7,20}"), "Phone: [removed]"),
    (re.compile(r"Office:.*?Urbana, IL \d{5}-\d{4}\s*<br>", re.S), ""),
    (re.compile(r"href=\"[^\"]*scholar\.google\.com/citations[^\"]*\""), "href=\"#\""),
    (re.compile(r"href=\"[^\"]*dblp\.uni-trier\.de[^\"]*\""), "href=\"#\""),
    (re.compile(r"href=\"[^\"]*twitter\.com/[^\"]*\""), "href=\"#\""),
    (re.compile(r"href=\"https?://gangw\.cs\.illinois\.edu[^\"]*\"", re.I), "href=\"#\""),
]

# Reference sub-pages become in-page anchors on the single Home page.
PAGE_MAP = {
    "news.html": "#news-archive",
    "publication.html": "#publications",
    "press.html": "#press",
    "activity.html": "#activities",
    "data.html": "#datasets",
    "talks.html": "#talks",
    "index.html": "#home",
}

# The site lives one directory below the site root: the canonical address is
# https://xx3416.github.io/gangwang/ and the site root only redirects there.
# The page's asset paths are rewritten for that location, because from
# /gangwang/ a relative "css/..." would resolve to /gangwang/css/...
SUBDIR = "gangwang"
CANONICAL = "https://xx3416.github.io/%s/" % SUBDIR

# References to the site's own assets, e.g. href="css/site.css" src="image/avatar.svg".
ASSET_REF = re.compile(
    r'((?:href|src)=")(?!#|https?:|//|mailto:|data:|javascript:)([^"/][^"]*)"')


def root_absolute(page):
    """Rewrite relative asset references to absolute paths from the site root."""
    return ASSET_REF.sub(r'\1/\2"', page)


def with_canonical(page):
    """Point the page at its canonical address."""
    tag = '  <link rel="canonical" href="%s">\n' % CANONICAL
    return page.replace('  <link rel="icon"', tag + '  <link rel="icon"', 1)


# The site root redirects to the canonical address. The fragment of the old
# URL is carried over, so https://xx3416.github.io/#publications still lands
# on the publications section.
REDIRECT_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Gang Wang</title>
  <link rel="canonical" href="%(canonical)s">
  <meta http-equiv="refresh" content="0; url=%(canonical)s#home">
  <script>
    window.location.replace("%(canonical)s" + (window.location.hash || "#home"));
  </script>
</head>
<body>
  <p>Redirecting to <a href="%(canonical)s">%(canonical)s</a>&hellip;</p>
</body>
</html>
""" % {"canonical": CANONICAL}


def read(name):
    with io.open(os.path.join(SRC, name), encoding="utf-8", errors="ignore") as fh:
        return fh.read()


def sanitize_snapshot(name, text):
    """Strip contact details from a reference snapshot and write it back."""
    for pattern, replacement in SNAPSHOT_CONTACT:
        text = pattern.sub(replacement, text)
    with io.open(os.path.join(SRC, name), "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def absolutize(fragment):
    """Point relative links at the reference site; map its sub-pages to anchors."""
    def repl(m):
        href = m.group(1)
        if href.startswith(("http://", "https://", "mailto:", "#", "javascript:", "data:")):
            return m.group(0)
        if href in PAGE_MAP:
            return 'href="%s"' % PAGE_MAP[href]
        return 'href="%s%s"' % (REF, href.lstrip("./"))
    return re.sub(r'href="([^"]+)"', repl, fragment)


def rebalance(fragment):
    """Re-serialize a fragment so <p> never nests and <div> always closes.

    The reference markup is sliced at arbitrary points and nests <p> inside
    <p>; browsers repair that silently but it makes the emitted HTML
    unbalanced. This normalizes it.
    """
    out = []
    div_depth = 0
    single = {"p": False, "em": False, "a": False}   # tags that may not nest
    pos = 0
    void = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}
    block_start = {"p", "div", "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5",
                   "h6", "table", "tr", "td", "th", "blockquote", "pre",
                   "section", "article", "hr", "br"}

    def close_single(tag):
        if single.get(tag):
            out.append("</%s>" % tag)
            single[tag] = False

    for m in re.finditer(r"<(/?)([a-zA-Z0-9]+)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*?)(/?)>", fragment):
        closing, tag, attrs, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if tag in ("script", "style"):
            continue
        # Keep the text between the previous tag and this one.
        out.append(fragment[pos:m.start()])
        pos = m.end()
        if closing:
            if tag in single:
                close_single(tag)
            elif tag == "div":
                if div_depth:
                    out.append("</div>")
                    div_depth -= 1
            else:
                out.append(m.group(0))
        else:
            if tag in block_start:
                close_single("p")
            if tag in single:
                close_single(tag)
                single[tag] = True
            if tag == "div" and not selfclose:
                div_depth += 1
            out.append(m.group(0))
            if tag in single and selfclose:
                single[tag] = False
    out.append(fragment[pos:])

    for tag in list(single):
        close_single(tag)
    out.append("</div>" * div_depth)
    return "".join(out)


def block(text, start, end, start_after=False):
    """Return the raw HTML between two markers."""
    i = text.index(start)
    if start_after:
        i += len(start)
    j = text.index(end, i)
    return text[i:j]


def clean(fragment):
    """Prepare a raw reference fragment for embedding."""
    fragment = absolutize(re.sub(r"\s+", " ", fragment.strip()))
    fragment = QUICKLINK.sub("", fragment)
    fragment = re.sub(r"\s{2,}", " ", fragment)
    if STRIP_REFERENCE_LINKS:
        # Unlink the papers/datasets that live on the reference site, so the
        # page carries no path back to it. The source markup mixes upper and
        # lower case tag names, so match case-insensitively.
        fragment = re.sub(r'<a href="%s[^"]*"[^>]*>(.*?)</a>' % re.escape(REF),
                          r'<span class="offlink">\1</span>', fragment, flags=re.S | re.I)
    return rebalance(fragment)


# --------------------------------------------------------------------------
# 1. Reference fragments
# --------------------------------------------------------------------------
home = strip_comments(sanitize_snapshot("gangw.html", read("gangw.html")))

# Every other snapshot is scrubbed on disk too, so no copy of the reference
# site keeps a contact detail or a back-link.
for _snapshot in ("publication.html", "press.html",
                  "activity.html", "data.html"):
    sanitize_snapshot(_snapshot, read(_snapshot))

news_html = block(home, "<h3>NEWS</h3>", "<h3>PRESS</h3>")
press_html = block(home, "<h3>PRESS</h3>", "<h3>LINKS</h3>")

# News and press entries are separated by a pushpin marker.
MARKER = r'<p><img src="fonts/glyphicons-336-pushpin\.png"[^>]*>\s*'


def entries(fragment):
    parts = [x for x in re.split(MARKER, fragment) if x.strip()]
    parts = [re.sub(r"</p>\s*$", "", x).strip() for x in parts]
    return [x for x in parts if x]


news_items = entries(news_html)
press_items = entries(press_html)

# The first news chunk carries the NEWS heading and the "Archived news" link.
news_items[0] = re.sub(r"^<h3>NEWS</h3>.*?</h4>", "", news_items[0], flags=re.S).strip()
# The first press chunk carries the PRESS heading.
press_items[0] = re.sub(r"^<h3>PRESS</h3>", "", press_items[0], flags=re.S).strip()


def has_text(item):
    """True when the entry carries any text (headings alone do not count)."""
    return bool(re.sub(r"<[^>]*>", "", item).replace("&nbsp;", " ").strip())


news_items = [i for i in news_items if has_text(i)]
press_items = [i for i in press_items if has_text(i)]

# Full publication list, grouped by year.
pub_body = block(strip_comments(read("publication.html")), '<div class="col-xs-12">', "</body>")
pub_groups = []
for m in re.finditer(r'<h5><font color="red">(\d{4})</font></h5>(.*?)(?=<h5><font color="red">|\Z)',
                     pub_body, flags=re.S):
    items = [i.strip() for i in re.findall(r"<li>(.*?)</li>", m.group(2), flags=re.S) if i.strip()]
    if items:
        pub_groups.append((m.group(1), items))

activity_body = block(strip_comments(read("activity.html")), '<div class="col-xs-12">', "</body>")
data_body = block(strip_comments(read("data.html")), '<div class="col-xs-12">', "</body>")


def sections(body, heading_pattern):
    """Split a sub-page into its <h5>-headed sections."""
    out = []
    for m in re.finditer(heading_pattern, body, flags=re.S):
        start = m.start()
        nxt = body.find("<h5", m.end())
        out.append(body[start:nxt if nxt != -1 else len(body)])
    return out


activity_sections = sections(activity_body, r"<h5>.*?</h5>")
data_sections = sections(data_body, r"<h5>.*?</h5>")

# --------------------------------------------------------------------------
# 2. Pieces of the page
# --------------------------------------------------------------------------
NAV = [
    ("#home", "Home"),
    ("#about", "About"),
    ("#publications", "Publications"),
    ("#press", "Press"),
    ("#activities", "Activities"),
    ("#datasets", "Datasets"),
    ("#news-archive", "News"),
]

BIO = """
            <p id="about">I am a <b>Research Scientist at ByteDance</b>, currently on <b>academic leave from the
            University of Illinois Urbana-Champaign (UIUC) since June 2025</b>. Before that, I was an
            Associate Professor of Computer Science in the
            <a href="https://siebelschool.illinois.edu">Siebel School of Computing and Data Science</a> at
            <a href="https://illinois.edu/">UIUC</a>, and the Associate Director of the
            <a href="https://asks.grainger.illinois.edu/">Capital One Illinois Center for Generative AI Safety, Knowledge Systems, and Cybersecurity (ASKS)</a>.
            I am also affiliated with the
            <a href="https://ece.illinois.edu/">Department of Electrical and Computer Engineering</a> (by courtesy),
            <a href="https://spri.engr.illinois.edu/">Security and Privacy Research at Illinois (SPRAI)</a>,
            <a href="http://informatics.web.illinois.edu/faculty-affiliates/">Informatics Programs of School of Information Sciences</a>, and
            <a href="https://csl.illinois.edu/">Coordinated Science Laboratory (CSL)</a>.
            My research aims to make it easier to build explainable and robust data-driven solutions to safeguard Internet systems and augment human's ability to perform security-related tasks. I am interested in a range of topics in Security and Privacy, Machine Learning, and Internet Measurement. My recent projects are focused on the security of social computing systems, cybercrime, adversarial machine learning, and machine learning explanation. I actively publish in conferences such as Usenix Security/CCS/NDSS/Oakland, IMC/WWW, and IMWUT/CHI.
            I am a recipient of the <b>NSF CAREER Award</b> (2018), <b>Amazon Research Award</b> (2021),
            <b>Google Faculty Research Award</b> (2017), <b>IMWUT Distinguished Paper Award</b> (2019),
            <b>ACM CCS Outstanding Paper Award</b> (2018), and
            <b>SIGMETRICS Best Practical Paper Award</b> (2013).</p>

            <p>
            I am part of the NSF AI Institute for Agent-based Cyber Threat Intelligence and Operation (<a href="https://action.ucsb.edu/research">ACTION</a>)
            and the Expedition Project for Learning Directed Operating System (<a href="https://ldos.utexas.edu">LDOS</a>).</p>

            <p>
            Before joining UIUC, I worked as an Assistant Professor at Virginia Tech from 2016 to 2019. I obtained my Ph.D. from UC Santa Barbara in 2016 under the supervision of Ben Y. Zhao and Heather Zheng. I received my bachelor's degree from Tsinghua University in 2010. I spent two summers at Microsoft Research Redmond in 2011 and 2014.</p>
"""

PUBLICATIONS = []
for year, items in pub_groups:
    if year in EXCLUDE_YEARS:
        continue
    PUBLICATIONS.append('<h4 class="pub-year">%s</h4>\n            <ul>' % year)
    for it in items:
        PUBLICATIONS.append("              <li>%s</li>" % clean(it))
    PUBLICATIONS.append("            </ul>")


def news_block(items):
    return "\n".join(
        '            <p class="news-item"><img src="fonts/glyphicons-336-pushpin.png" width="10"> %s</p>'
        % clean(i) for i in items)


PRESS_BLOCK = "\n".join('            <p>%s</p>' % clean(p) for p in press_items)
ACTIVITY_BLOCK = "\n".join(clean(s) for s in activity_sections)
DATA_BLOCK = "\n".join(clean(s) for s in data_sections)

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>Gang Wang</title>
  <meta name="description" content="Personal homepage of Gang Wang, a Research Scientist at ByteDance and Associate Professor of Computer Science at the University of Illinois Urbana-Champaign (on academic leave since June 2025).">
  <meta name="author" content="Gang Wang">
  <link rel="icon" type="image/svg+xml" href="image/avatar.svg">

  <link href="css/bootstrap.css" rel="stylesheet" media="screen">
  <link href="css/non-responsive.css" rel="stylesheet">
  <link href="css/site.css" rel="stylesheet" media="screen">
  <script src="css/jquery-1.10.2.min.js"></script>
  <script src="css/bootstrap.min.js"></script>
</head>

<body id="home">

  <div class="navbar navbar-default navbar-fixed-top">
    <div class="container">
      <a class="navbar-brand" href="#home">Gang Wang</a>
      <a class="navbar-brand affiliation-brand" href="#home"><span class="affiliation">ByteDance</span></a>

      <button class="navbar-toggle collapsed" type="button" data-toggle="collapse" data-target="#navbar-main" aria-expanded="false">
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>

      <div class="navbar-collapse collapse" id="navbar-main">
        <ul class="nav navbar-nav navbar-right">
%s
        </ul>
      </div>
    </div>
  </div>

  <div class="container page-wrap">

    <header class="profile-header">
      <img class="avatar-lg" src="image/avatar.svg" alt="Gang Wang" />
      <div class="profile-text">
        <h1>Gang Wang</h1>
        <p class="profile-role">Research Scientist &middot; ByteDance</p>
        <p class="profile-note">On academic leave from the University of Illinois Urbana-Champaign since June 2025</p>
      </div>
    </header>

    <section id="about" class="page-section">
      <h2>About</h2>
%s
    </section>

    <section id="publications" class="page-section">
      <h2>Publications</h2>
      <p class="text-muted"><small>The documents listed below have been provided by the contributing authors as a means to ensure timely dissemination of scholarly and technical work on a noncommercial basis. Copyright and all rights therein are maintained by the authors or by other copyright holders.</small></p>
      <p class="text-muted"><small>
        <span class="label label-success">C</span> Conference Proceeding |
        <span class="label label-danger">J</span> Journal Article |
        <span class="label label-default">W</span> Workshop Proceeding
      </small></p>
%s
    </section>

    <section id="press" class="page-section">
      <h2>Press</h2>
%s
    </section>

    <section id="activities" class="page-section">
      <h2>Professional Activities</h2>
%s
    </section>

    <section id="datasets" class="page-section">
      <h2>Datasets &amp; Tools</h2>
%s
    </section>

    <section id="news-archive" class="page-section">
      <h2>News</h2>
%s
    </section>
  </div>

  <footer class="site-footer">
    <div class="container">
      <p class="text-muted">Copyright &copy; Gang Wang &middot; css design: Thomas Park &middot; hosted on GitHub Pages</p>
    </div>
  </footer>

</body>
</html>
"""

PAGE = PAGE % (
    "\n".join('          <li><a href="%s">%s</a></li>' % (href, label) for href, label in NAV),
    BIO,
    "\n".join(PUBLICATIONS),
    PRESS_BLOCK,
    ACTIVITY_BLOCK,
    DATA_BLOCK,
    news_block(news_items[NEWS_SKIP:]),
)

# The site lives one directory below the site root; the root itself is a
# redirect stub, so the site has exactly one address:
# https://xx3416.github.io/gangwang/
subdir = os.path.join(OUT, SUBDIR)
if not os.path.isdir(subdir):
    os.makedirs(subdir)
subpage = root_absolute(with_canonical(PAGE))
with io.open(os.path.join(subdir, "index.html"), "w", encoding="utf-8") as fh:
    fh.write(subpage)

with io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
    fh.write(REDIRECT_PAGE)

print("%s/index.html written: %d bytes" % (SUBDIR, len(subpage.encode("utf-8"))))
print("index.html written: %d bytes (redirect to %s)" % (
    len(REDIRECT_PAGE.encode("utf-8")), CANONICAL))
print("  news      : %d shown (%d skipped, oldest shown: %s)" % (
    len(news_items) - NEWS_SKIP, NEWS_SKIP,
    (re.search(r"<strong>([^<]+)</strong>", news_items[NEWS_SKIP]).group(1)
     if NEWS_SKIP < len(news_items) else "n/a")))
print("  press     : %d" % len(press_items))
kept = [(y, i) for y, i in pub_groups if y not in EXCLUDE_YEARS]
print("  pubs      : %d year groups, %d entries (excluded years: %s)" % (
    len(kept), sum(len(i) for _, i in kept), ", ".join(sorted(EXCLUDE_YEARS)) or "none"))
print("  activity  : %d sections" % len(activity_sections))
print("  datasets  : %d sections" % len(data_sections))
