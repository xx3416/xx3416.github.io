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

# Reference sub-pages become in-page anchors on the single Home page.
PAGE_MAP = {
    "news.html": "#news-archive",
    "publication.html": "#publications",
    "press.html": "#press",
    "students.html": "#students",
    "activity.html": "#activities",
    "data.html": "#datasets",
    "talks.html": "#talks",
    "index.html": "#home",
}


def read(name):
    with io.open(os.path.join(SRC, name), encoding="utf-8", errors="ignore") as fh:
        return fh.read()


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
    return rebalance(absolutize(re.sub(r"\s+", " ", fragment.strip())))


# --------------------------------------------------------------------------
# 1. Reference fragments
# --------------------------------------------------------------------------
home = strip_comments(read("gangw.html"))

news_html = block(home, "<h3>NEWS</h3>", "<h3>PRESS</h3>")
press_html = block(home, "<h3>PRESS</h3>", "<h3>LINKS</h3>")
class_html = block(home, "<h3>CLASS</h3>", "<h3>NEWS</h3>")

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

students_body = block(strip_comments(read("students.html")), '<div class="col-xs-12">', "</body>")
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


students_sections = sections(students_body, r"<h5>(?:<strong>)?.*?</h5>")
activity_sections = sections(activity_body, r"<h5>.*?</h5>")
data_sections = sections(data_body, r"<h5>.*?</h5>")

# --------------------------------------------------------------------------
# 2. Pieces of the page
# --------------------------------------------------------------------------
NAV = [
    ("#home", "Home"),
    ("#publications", "Publications"),
    ("#press", "Press"),
    ("#students", "Students"),
    ("#activities", "Activities"),
    ("#datasets", "Datasets"),
    ("#cv", "CV"),
]

LINKS = """
        <p>
          <a href="https://scholar.google.com/citations?user=-DfTtxgAAAAJ" class="btn btn-primary btn-sm">Google Scholar</a>
          <a href="https://dblp.uni-trier.de/pers/hd/w/Wang_0011:Gang" class="btn btn-primary btn-sm">DBLP</a>
          <a href="https://twitter.com/ffmagicbean" class="btn btn-primary btn-sm">Twitter</a>
          <a href="https://github.com/xx3416" class="btn btn-primary btn-sm">GitHub</a>
        </p>
"""

CLASS_BLOCK = """<h3>CLASS</h3>
         <p><small>(taught at UIUC; on academic leave since June 2025)</small></p>
         <p>%s</p>""" % re.sub(r"\s+", " ", class_html.split("</p>")[0].replace("<h3>CLASS</h3>", "")
                             .replace("<p>", "", 1).strip())

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

SPONSORS = """<h3>SPONSORS</h3>
            <p class="sponsor-logos">
              <img src="image/nsf1.jpg" width="100" alt="NSF" /><br>
              <img src="image/google.jpg" width="120" alt="Google" /><br>
              <img src="image/amazon.jpg" width="120" alt="Amazon" /><br>
              <img src="image/ibm.png" width="100" alt="IBM" /><br>
              <img src="image/jump-logo.png" width="120" alt="Jump" /><br>
              <img src="image/nih.png" width="80" alt="NIH" /><br>
              <img src="image/massaitc.jpeg" width="100" alt="MIT CSAIL" /><br>
              <img src="image/ebay-logo.png" width="100" alt="eBay" /><br>
              <img src="image/Capital-One.png" width="140" alt="Capital One" />
            </p>"""

PUBLICATIONS = []
for year, items in pub_groups:
    PUBLICATIONS.append('<h4 class="pub-year">%s</h4>\n            <ul>' % year)
    for it in items:
        PUBLICATIONS.append("              <li>%s</li>" % clean(it))
    PUBLICATIONS.append("            </ul>")


def news_block(items):
    return "\n".join(
        '            <p class="news-item"><img src="fonts/glyphicons-336-pushpin.png" width="10"> %s</p>'
        % clean(i) for i in items)


PRESS_BLOCK = "\n".join('            <p>%s</p>' % clean(p) for p in press_items)
STUDENTS_BLOCK = "\n".join(clean(s) for s in students_sections)
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
      <a class="navbar-brand" href="#home"><center><font color="white">Gang Wang</font></center></a>
      <a class="navbar-brand" href="#home"><center><span class="affiliation">ByteDance</span></center></a>

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

  <div class="container">
    <div class="bs-docs-section">
      <div class="row">

        <!-- ============================= SIDEBAR ============================= -->
        <div class="col-xs-3">
          <div class="bs-component">
            <a href="image/avatar.svg"><img class="avatar" src="image/avatar.svg" width="200" height="200" alt="Gang Wang" /></a>
          </div>

          <div class="bs-component">
            <h3>CONTACT</h3>
            <p><b>ByteDance</b> &mdash; Research<br>
                   <span class="muted-note">On academic leave from UIUC since June 2025</span><br><br>
                   Office: Thomas M. Siebel Center<br>
                   201 North Goodwin Avenue<br>
                   MC 258, Room 4316<br>
                   Urbana, IL 61801-2302<br><br>
                   Phone: 217-244-1008</p>
%s
          </div>

          <div class="bs-component">
%s
          </div>

          <div class="bs-component">
            <h3>NEWS</h3>
%s
            <p class="small"><a href="#news-archive">(Archived news)</a></p>
          </div>

          <div class="bs-component">
%s
          </div>
        </div>

        <!-- ============================== MAIN ============================== -->
        <div class="col-xs-9 border-left">
          <div class="bs-component">
%s
          </div>

          <div class="bs-component" id="publications">
            <h3>Publications</h3>
            <p class="text-muted"><small>The documents listed below have been provided by the contributing authors as a means to ensure timely dissemination of scholarly and technical work on a noncommercial basis. Copyright and all rights therein are maintained by the authors or by other copyright holders.</small></p>
            <p class="text-muted"><small>
              <span class="label label-success">C</span> Conference Proceeding |
              <span class="label label-danger">J</span> Journal Article |
              <span class="label label-default">W</span> Workshop Proceeding
            </small></p>
%s
          </div>

          <div class="bs-component" id="press">
            <h3>Press</h3>
%s
          </div>

          <div class="bs-component" id="students">
            <h3>Students</h3>
%s
          </div>

          <div class="bs-component" id="activities">
            <h3>Professional Activities</h3>
%s
          </div>

          <div class="bs-component" id="datasets">
            <h3>Datasets &amp; Tools</h3>
%s
          </div>

          <div class="bs-component" id="news-archive">
            <h3>Archived News</h3>
%s
          </div>

          <div class="bs-component" id="cv">
            <h3>CV</h3>
            <p><a href="CV.pdf" class="btn btn-primary btn-sm">Download CV (PDF)</a></p>
          </div>

          <div class="bs-component" id="links">
            <h3>Links</h3>
            <p>
              <a href="https://github.com/xx3416">GitHub</a> &middot;
              <a href="https://scholar.google.com/citations?user=-DfTtxgAAAAJ">Google Scholar</a> &middot;
              <a href="https://dblp.uni-trier.de/pers/hd/w/Wang_0011:Gang">DBLP</a> &middot;
              <a href="https://twitter.com/ffmagicbean">Twitter</a>
            </p>
          </div>
        </div>
      </div>
    </div>
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
    LINKS,
    CLASS_BLOCK,
    news_block(news_items[:12]),
    SPONSORS,
    BIO,
    "\n".join(PUBLICATIONS),
    PRESS_BLOCK,
    STUDENTS_BLOCK,
    ACTIVITY_BLOCK,
    DATA_BLOCK,
    news_block(news_items[12:]),
)

with io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
    fh.write(PAGE)

print("index.html written: %d bytes" % len(PAGE.encode("utf-8")))
print("  news      : %d (%d sidebar / %d archive)" % (
    len(news_items), min(12, len(news_items)), max(0, len(news_items) - 12)))
print("  press     : %d" % len(press_items))
print("  pubs      : %d year groups, %d entries" % (
    len(pub_groups), sum(len(i) for _, i in pub_groups)))
print("  students  : %d sections" % len(students_sections))
print("  activity  : %d sections" % len(activity_sections))
print("  datasets  : %d sections" % len(data_sections))
