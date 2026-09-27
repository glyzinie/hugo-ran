"""Check the public HTML produced by this Hugo theme.

Run with ``uv run --no-cache --no-project python tests/test_seo_output.py``. Set
``HUGO_BINARY`` to exercise another supported Hugo release. The fixture is a
small site assembled in a temporary directory; it never needs the network.
"""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


THEME = Path(__file__).resolve().parents[1]
BASE_URL = "https://example.test/blog/"
EXPLICIT_DESCRIPTION = (
    "This manually written page description explains the site, its editorial scope, "
    "the evidence behind the articles, and the contact route for readers. "
    "It intentionally exceeds one hundred and sixty characters."
)
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


@dataclass
class Element:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Element | str] = field(default_factory=list)

    def all(self, tag: str) -> list[Element]:
        found: list[Element] = []
        for child in self.children:
            if isinstance(child, Element):
                if child.tag == tag:
                    found.append(child)
                found.extend(child.all(tag))
        return found

    def text(self) -> str:
        return "".join(
            child if isinstance(child, str) else child.text() for child in self.children
        )


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("document")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = Element(tag, {key: value or "" for key, value in attrs})
        self.stack[-1].children.append(element)
        if tag not in VOID_TAGS:
            self.stack.append(element)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def parse_html(path: Path) -> Element:
    parser = DocumentParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser.root


def output_path(public: Path, url: str) -> Path:
    parsed = urlparse(url)
    base_path = urlparse(BASE_URL).path
    if parsed.netloc != urlparse(BASE_URL).netloc or not parsed.path.startswith(base_path):
        raise AssertionError(f"URL is outside the fixture site: {url}")
    relative = parsed.path.removeprefix(base_path)
    return public / (relative + "index.html" if not relative or relative.endswith("/") else relative)


def png(width: int = 4, height: int = 3) -> bytes:
    """Produce a real RGB PNG so Hugo can inspect image dimensions."""

    def chunk(name: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + name + data
            + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
        )

    rows = b"".join(b"\x00" + b"\x20\x80\xc0" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )


def write(root: Path, relative: str, contents: str | bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(contents, bytes):
        path.write_bytes(contents)
    else:
        path.write_text(contents, encoding="utf-8")


def build_site(root: Path, *, minimal: bool = False) -> Path:
    site = root / ("minimal" if minimal else "full")
    theme_link = site / "themes" / "ran"
    theme_link.parent.mkdir(parents=True)
    theme_link.symlink_to(THEME, target_is_directory=True)
    common = '''baseURL = "https://example.test/blog/"
title = "Test Site"
theme = "ran"
languageCode = "en"
enableRobotsTXT = true

[pagination]
pagerSize = 2

[taxonomies]
tag = "tags"

[outputs]
page = ["HTML", "AMP"]
section = ["HTML", "AMP"]
'''
    if minimal:
        write(site, "hugo.toml", common + '''
[params]
author = "Site String Author"
''')
        write(site, "content/about.md", '''---
title: Plain information
---
Plain information without optional site or page metadata.
''')
    else:
        write(site, "hugo.toml", common.replace('languageCode = "en"', 'languageCode = "ja-JP"') + '''
[params]
description = "サイト共通の説明"
mainSections = ["posts"]
robots = "index, follow"
thumbnail = "/images/static.png"
thumbnailAlt = "Site cover"

[params.author]
name = "Site Author"
url = "https://example.test/author/"

[frontmatter]
date = ["date"]
publishDate = ["publishDate", "date"]
lastmod = ["lastmod"]

[markup.goldmark.renderer]
unsafe = true
''')
        write(site, "content/_index.md", '''---
title: ホーム
description: ホーム固有の説明
---
サイトの案内文。
''')
        write(site, "content/posts/_index.md", '''---
title: 技術記事
description: 技術記事一覧の固有説明
---
検証記録を集めた記事一覧の導入文。
''')
        write(site, "content/tags/_index.md", '''---
title: タグ別の記事
description: タグ一覧の固有説明
---
話題別に記事を探せます。
''')
        write(site, "content/tags/seo/_index.md", '''---
title: SEO
description: SEOタグ固有の説明
---
検索に関する記事をまとめています。
''')
        write(site, "content/about.md", '''---
title: このサイトについて
description: 運営者とサイトの説明
date: 2025-04-01T10:00:00+09:00
---
このサイトの目的と運営者を説明します。
''')
        write(site, "content/posts/feature/index.md", '''---
title: 画像と検索の検証
date: 2025-01-02T09:00:00+09:00
publishDate: 2025-01-04T09:00:00+09:00
lastmod: 2025-02-03T10:00:00+09:00
description: ""
author: Feature Author
thumbnail: /images/static.png
tags: [SEO, AI Search]
---
<!--more-->
画像の読み込みと検索結果を実機で確認した記録です。条件と結果を本文に示します。

![Assets diagram](images/asset.png "Assets title")

![Static diagram](/images/static.png)

![Bundle diagram](bundle.png)
''')
        write(site, "assets/images/asset.png", png())
        write(site, "static/images/static.png", png())
        write(site, "content/posts/feature/bundle.png", png())
        write(site, "content/posts/dated.md", '''---
title: 公開日と更新日
date: 2025-03-01T10:00:00+09:00
lastmod: 2025-03-05T11:00:00+09:00
tags: [SEO]
---
公開後に内容を検証して更新しました。
''')
        write(site, "content/posts/undated.md", '''---
title: 日付のない記事
tags: [SEO]
---
日付がない状態でも誤った日時を表示しません。
''')
        write(site, "content/posts/more.md", '''---
title: 追加の記事
date: 2025-03-02T10:00:00+09:00
---
ページ分割を確認する記事です。
''')
        write(site, "content/posts/last.md", '''---
title: 最後の記事
date: 2025-03-03T10:00:00+09:00
---
ページ分割を確認する記事です。
''')
        write(site, "content/posts/private.md", '''---
title: 検索対象外の記事
date: 2025-03-04T10:00:00+09:00
noindex: true
---
検索対象から外すページです。
''')
        write(site, "content/posts/mapped.md", '''---
title: 著者を個別指定した記事
date: 2025-03-06T10:00:00+09:00
author:
  name: Mapped Author
  url: https://example.test/people/mapped/
---
執筆者をこの記事に指定しました。
''')
        write(site, "content/posts/updated-only.md", '''---
title: 更新日のみ指定した記事
lastmod: 2025-05-01T11:00:00+09:00
---
公開日の入力がない更新記録です。
''')
        write(site, "content/posts/summary.md", '''---
title: 出典と画像を含む要約
date: 2025-08-01T10:00:00+09:00
thumbnail: /images/missing.png
thumbnailAlt: Missing page cover
---
概要では[原典](https://example.test/evidence/)を参照します。

![Summary figure](/images/static.png)

<iframe src="https://example.test/embed/" title="Example embed"></iframe>

<!--more-->
本文では検証方法を詳しく説明します。
''')
        write(site, "content/about-special.md", f'''---
title: 明示設定の固定ページ
schemaType: AboutPage
author: false
description: "{EXPLICIT_DESCRIPTION}"
---
ページ固有の設定を検証します。
''')

    destination = root / ("minimal-public" if minimal else "full-public")
    binary = os.environ.get("HUGO_BINARY", "hugo")
    if not shutil.which(binary):
        raise RuntimeError(f"Hugo executable not found: {binary}")
    env = os.environ.copy()
    env["HUGO_RESOURCEDIR"] = str(root / ("minimal-resources" if minimal else "full-resources"))
    result = subprocess.run(
        [binary, "--source", str(site), "--destination", str(destination),
         "--cacheDir", str(root / "hugo-cache"), "--noBuildLock"],
        text=True,
        capture_output=True,
        env=env,
        timeout=90,
        check=False,
    )
    if result.returncode:
        raise AssertionError(
            f"Hugo failed for {'minimal' if minimal else 'full'} fixture "
            f"({binary}, exit {result.returncode}):\n{result.stdout}\n{result.stderr}"
        )
    return destination


def build_multilingual_site(root: Path, *, ugly: bool = False) -> Path:
    site = root / ("multilingual-ugly" if ugly else "multilingual")
    theme_link = site / "themes" / "ran"
    theme_link.parent.mkdir(parents=True)
    theme_link.symlink_to(THEME, target_is_directory=True)
    ugly_setting = "uglyURLs = true" if ugly else ""
    pager_path = 'path = "p"' if ugly else ""
    language_subdir = "false" if ugly else "true"
    write(site, "hugo.toml", f'''baseURL = "https://example.test/blog/"
theme = "ran"
defaultContentLanguage = "en"
defaultContentLanguageInSubdir = {language_subdir}
{ugly_setting}

[pagination]
pagerSize = 1
{pager_path}

[outputs]
home = ["HTML", "AMP"]
section = ["HTML", "AMP"]

[params]
mainSections = ["posts"]

[languages.en]
languageCode = "en-US"
languageName = "English"
title = "English Site"
contentDir = "content/en"
weight = 1

[languages.ja]
languageCode = "ja-JP"
languageName = "日本語サイト"
title = "日本語サイト"
contentDir = "content/ja"
weight = 2
''')
    for language, home_title, section_title, titles, summaries in (
        ("en", "Home", "Posts", ("Alpha", "Beta"), ("First article.", "Second article.")),
        ("ja", "ホーム", "記事", ("アルファ", "ベータ"), ("最初の記事。", "次の記事。")),
    ):
        write(site, f"content/{language}/_index.md", f'''---
title: {home_title}
---
{home_title} introduction.
''')
        write(site, f"content/{language}/posts/_index.md", f'''---
title: {section_title}
---
{section_title} introduction.
''')
        for index, slug in enumerate(("alpha", "beta"), start=1):
            write(site, f"content/{language}/posts/{slug}.md", f'''---
title: {titles[index - 1]}
date: 2025-06-0{index}T10:00:00+09:00
---
{summaries[index - 1]}
''')

    destination = root / ("multilingual-ugly-public" if ugly else "multilingual-public")
    binary = os.environ.get("HUGO_BINARY", "hugo")
    env = os.environ.copy()
    env["HUGO_RESOURCEDIR"] = str(root / ("multilingual-ugly-resources" if ugly else "multilingual-resources"))
    result = subprocess.run(
        [binary, "--source", str(site), "--destination", str(destination),
         "--cacheDir", str(root / "hugo-cache"), "--noBuildLock"],
        text=True,
        capture_output=True,
        env=env,
        timeout=90,
        check=False,
    )
    if result.returncode:
        raise AssertionError(
            f"Hugo failed for multilingual fixture ({binary}, exit {result.returncode}):"
            f"\n{result.stdout}\n{result.stderr}"
        )
    return destination


class SEOOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory(prefix="hugo-ran-seo-")
        cls.root = Path(cls.tmp.name)
        try:
            cls.public = build_site(cls.root)
            cls.minimal_public = build_site(cls.root, minimal=True)
            cls.multilingual_public = build_multilingual_site(cls.root)
            cls.multilingual_ugly_public = build_multilingual_site(cls.root, ugly=True)
        except BaseException:
            cls.tmp.cleanup()
            raise
        cls.parsed: dict[Path, Element] = {}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def doc(self, relative: str, *, minimal: bool = False, multilingual: bool = False) -> Element:
        self.assertFalse(minimal and multilingual)
        public = self.multilingual_public if multilingual else self.minimal_public if minimal else self.public
        path = public / relative
        self.assertTrue(path.is_file(), f"Expected Hugo output: {path}")
        if path not in self.parsed:
            self.parsed[path] = parse_html(path)
        return self.parsed[path]

    def one(self, doc: Element, tag: str, **attrs: str) -> Element:
        matches = [
            node for node in doc.all(tag)
            if all(node.attrs.get(key) == value for key, value in attrs.items())
        ]
        self.assertEqual(len(matches), 1, f"Expected one {tag} {attrs}, got {len(matches)}")
        return matches[0]

    def meta(self, doc: Element, key: str, *, property: bool = False) -> str | None:
        attribute = "property" if property else "name"
        matches = [node for node in doc.all("meta") if node.attrs.get(attribute) == key]
        self.assertLessEqual(len(matches), 1, f"Duplicate {key} metadata")
        return matches[0].attrs.get("content") if matches else None

    def canonical(self, doc: Element) -> str:
        return self.one(doc, "link", rel="canonical").attrs["href"]

    def schema(self, doc: Element, kind: str) -> dict:
        nodes: list[dict] = []
        for script in doc.all("script"):
            if script.attrs.get("type") == "application/ld+json":
                data = json.loads(script.text())
                objects = data if isinstance(data, list) else [data]
                for obj in objects:
                    nodes.extend(obj.get("@graph", [obj]))
        matches = [
            obj for obj in nodes
            if kind in (obj.get("@type") if isinstance(obj.get("@type"), list)
                        else [obj.get("@type")])
        ]
        self.assertEqual(len(matches), 1, f"Expected one {kind} schema; got {nodes}")
        return matches[0]

    def test_paginated_list_identifies_itself(self) -> None:
        doc = self.doc("posts/page/2/index.html")
        expected = BASE_URL + "posts/page/2/"
        self.assertEqual(self.canonical(doc), expected)
        self.assertEqual(self.meta(doc, "og:url", property=True), expected)
        self.assertNotEqual(self.canonical(doc), BASE_URL + "posts/")

    def test_amp_and_html_identify_the_same_article(self) -> None:
        normal = self.doc("posts/feature/index.html")
        amp = self.doc("amp/posts/feature/index.html")
        expected = BASE_URL + "posts/feature/"
        self.assertEqual(self.canonical(normal), expected)
        self.assertEqual(self.canonical(amp), expected)
        self.assertEqual(self.meta(amp, "og:url", property=True), expected)
        for doc in (normal, amp):
            article = self.schema(doc, "BlogPosting")
            entity = article.get("mainEntityOfPage")
            self.assertEqual(entity.get("@id") if isinstance(entity, dict) else entity, expected)

    def test_schema_matches_page_type(self) -> None:
        for path, expected in (
            ("index.html", "WebSite"),
            ("posts/index.html", "CollectionPage"),
            ("tags/index.html", "CollectionPage"),
            ("tags/seo/index.html", "CollectionPage"),
            ("posts/feature/index.html", "BlogPosting"),
            ("about/index.html", "WebPage"),
        ):
            with self.subTest(path=path):
                self.schema(self.doc(path), expected)

    def test_real_dates_and_author_are_consistent(self) -> None:
        doc = self.doc("posts/feature/index.html")
        article = self.schema(doc, "BlogPosting")
        self.assertTrue(article["datePublished"].startswith("2025-01-04"))
        self.assertTrue(article["dateModified"].startswith("2025-02-03"))
        self.assertEqual(article["author"]["name"], "Feature Author")
        byline = self.one(doc, "div", **{"class": "meta"}).text()
        self.assertIn("Feature Author", byline)
        self.assertNotIn("Site Author", byline)
        self.assertNotIn("0001-01-01", doc.text())
        times = [node.attrs.get("datetime", "") for node in doc.all("time")]
        self.assertTrue(any(value.startswith("2025-01-04") for value in times))
        self.assertTrue(any(value.startswith("2025-02-03") for value in times))

    def test_author_map_and_explicit_author_opt_out(self) -> None:
        mapped = self.doc("posts/mapped/index.html")
        author = self.schema(mapped, "BlogPosting")["author"]
        self.assertEqual(author["name"], "Mapped Author")
        self.assertEqual(author["url"], "https://example.test/people/mapped/")
        self.assertEqual(self.meta(mapped, "author"), "Mapped Author")
        self.assertIn("Mapped Author", self.one(mapped, "div", **{"class": "meta"}).text())

        opt_out = self.doc("about-special/index.html")
        self.assertNotIn("author", self.schema(opt_out, "AboutPage"))
        self.assertIsNone(self.meta(opt_out, "author"))
        self.assertFalse([node for node in opt_out.all("span") if "byline" in node.attrs.get("class", "")])

    def test_updated_only_page_has_only_a_modified_date(self) -> None:
        doc = self.doc("posts/updated-only/index.html")
        article = self.schema(doc, "BlogPosting")
        self.assertNotIn("datePublished", article)
        self.assertTrue(article["dateModified"].startswith("2025-05-01"))
        times = [node.attrs.get("datetime", "") for node in doc.all("time")]
        self.assertEqual(len(times), 1)
        self.assertTrue(times[0].startswith("2025-05-01"))

    def test_undated_page_never_invents_year_one(self) -> None:
        path = "posts/undated/index.html"
        doc = self.doc(path)
        self.assertFalse(
            "0001-01-01" in (self.public / path).read_text(encoding="utf-8"),
            "An undated page rendered the zero date",
        )
        article = self.schema(doc, "BlogPosting")
        self.assertNotIn("datePublished", article)
        self.assertNotIn("dateModified", article)
        self.assertFalse(doc.all("time"))

    def test_description_uses_content_and_list_front_matter(self) -> None:
        article = self.doc("posts/feature/index.html")
        description = self.meta(article, "description")
        self.assertIn("画像の読み込みと検索結果", description or "")
        self.assertEqual(self.meta(article, "og:description", property=True), description)
        self.assertEqual(
            self.meta(self.doc("posts/index.html"), "description"),
            "技術記事一覧の固有説明",
        )
        self.assertEqual(
            self.meta(self.doc("tags/seo/index.html"), "description"),
            "SEOタグ固有の説明",
        )
        explicit = self.doc("about-special/index.html")
        self.assertGreater(len(EXPLICIT_DESCRIPTION), 160)
        self.assertEqual(self.meta(explicit, "description"), EXPLICIT_DESCRIPTION)
        self.assertEqual(self.schema(explicit, "AboutPage")["description"], EXPLICIT_DESCRIPTION)

    def test_images_have_alt_dimensions_and_loading_priority(self) -> None:
        doc = self.doc("posts/feature/index.html")
        body = self.one(doc, "div", **{"class": "entry"})
        images = body.all("img")
        self.assertEqual(len(images), 3)
        for image, alt, suffix in zip(
            images,
            ("Assets diagram", "Static diagram", "Bundle diagram"),
            ("/images/asset.png", "/images/static.png", "/posts/feature/bundle.png"),
        ):
            with self.subTest(alt=alt):
                self.assertEqual(image.attrs.get("alt"), alt)
                self.assertEqual(image.attrs.get("width"), "4")
                self.assertEqual(image.attrs.get("height"), "3")
                self.assertTrue(urlparse(image.attrs["src"]).path.endswith(suffix))
                image_path = urlparse(urljoin(BASE_URL, image.attrs["src"])).path
                self.assertTrue(image_path.startswith("/blog/"))
                self.assertTrue((self.public / image_path.removeprefix("/blog/")).is_file())
        self.assertEqual(images[0].attrs.get("loading"), "eager")
        self.assertEqual([image.attrs.get("loading") for image in images[1:]], ["lazy", "lazy"])

    def test_amp_images_keep_alt_and_dimensions(self) -> None:
        doc = self.doc("amp/posts/feature/index.html")
        body = self.one(doc, "div", **{"class": "entry"})
        images = body.all("amp-img")
        self.assertEqual(len(images), 3)
        for image, alt in zip(images, ("Assets diagram", "Static diagram", "Bundle diagram")):
            with self.subTest(alt=alt):
                self.assertEqual(image.attrs.get("alt"), alt)
                self.assertEqual(image.attrs.get("width"), "4")
                self.assertEqual(image.attrs.get("height"), "3")

    def test_lists_have_their_own_heading_and_introduction(self) -> None:
        for path, heading, introduction in (
            ("posts/index.html", "技術記事", "検証記録を集めた記事一覧の導入文"),
            ("tags/index.html", "タグ別の記事", "話題別に記事を探せます"),
            ("tags/seo/index.html", "SEO", "検索に関する記事をまとめています"),
        ):
            with self.subTest(path=path):
                main = self.one(self.doc(path), "main")
                headings = [node.text().strip() for node in main.all("h1")]
                self.assertEqual(headings, [heading])
                self.assertIn(introduction, main.text())
                if path != "tags/index.html":
                    self.assertTrue(main.all("h2"), "Article links should be secondary headings")

    def test_tag_links_use_the_term_permalink(self) -> None:
        doc = self.doc("posts/feature/index.html")
        matches = [node for node in doc.all("a") if node.text().strip() == "SEO"]
        self.assertTrue(matches)
        self.assertTrue(any(
            urljoin(BASE_URL, node.attrs.get("href", "")) == BASE_URL + "tags/seo/"
            for node in matches
        ))

    def test_article_breadcrumbs_connect_home_section_and_article(self) -> None:
        doc = self.doc("posts/feature/index.html")
        breadcrumb = self.schema(doc, "BreadcrumbList")
        items = breadcrumb["itemListElement"]
        self.assertEqual([item["position"] for item in items], [1, 2, 3])
        urls = [
            item.get("item", {}).get("@id") if isinstance(item.get("item"), dict)
            else item.get("item") for item in items
        ]
        self.assertEqual(urls[:2], [BASE_URL, BASE_URL + "posts/"])
        self.assertTrue(all(item.get("name") for item in items))
        main = self.one(doc, "main")
        current = [
            node for node in main.all("span") if node.attrs.get("aria-current") == "page"
        ]
        self.assertEqual(len(current), 1)
        self.assertIn("画像と検索の検証", current[0].text())

    def test_noindex_and_robots_are_explicit(self) -> None:
        private = self.doc("posts/private/index.html")
        directives = (self.meta(private, "robots") or "").lower().replace(" ", "")
        self.assertIn("noindex", directives.split(","))
        self.assertNotIn("index", directives.split(","))
        self.assertNotIn("all", directives.split(","))
        amp_private = self.doc("amp/posts/private/index.html")
        self.assertIn("noindex", (self.meta(amp_private, "robots") or "").lower())
        ordinary = (self.meta(self.doc("posts/feature/index.html"), "robots") or "").lower()
        self.assertIn("index", ordinary)
        self.assertNotIn("noindex", ordinary)
        self.assertIn("noindex", (self.meta(self.doc("404.html"), "robots") or "").lower())
        robots_path = self.public / "robots.txt"
        self.assertTrue(robots_path.is_file())
        robots = robots_path.read_text(encoding="utf-8").lower()
        self.assertIn("user-agent:", robots)
        self.assertNotIn("disallow: /\n", robots)

    def test_sitemap_has_only_canonical_page_urls(self) -> None:
        root = ET.parse(self.public / "sitemap.xml").getroot()
        locations = {
            element.text for element in root.iter() if element.tag.endswith("}loc") or element.tag == "loc"
        }
        self.assertIn(BASE_URL + "posts/feature/", locations)
        self.assertIn(BASE_URL + "tags/seo/", locations)
        self.assertNotIn(BASE_URL + "amp/posts/feature/", locations)

    def test_real_thumbnail_is_used_in_social_and_article_data(self) -> None:
        doc = self.doc("posts/feature/index.html")
        expected = BASE_URL + "images/static.png"
        self.assertEqual(self.meta(doc, "og:image", property=True), expected)
        images = self.schema(doc, "BlogPosting")["image"]
        if not isinstance(images, list):
            images = [images]
        urls = [item.get("url") if isinstance(item, dict) else item for item in images]
        self.assertIn(expected, urls)

    def test_missing_page_thumbnail_uses_site_image_and_site_alt(self) -> None:
        doc = self.doc("posts/summary/index.html")
        self.assertEqual(self.meta(doc, "og:image", property=True), BASE_URL + "images/static.png")
        self.assertEqual(self.meta(doc, "og:image:alt", property=True), "Site cover")
        self.assertEqual(self.meta(doc, "twitter:image:alt"), "Site cover")
        self.assertNotIn("Missing page cover", (self.public / "posts/summary/index.html").read_text())

    def test_list_summaries_are_safe_for_amp_and_retain_html_links(self) -> None:
        html_list = self.doc("posts/index.html")
        amp_href = self.one(html_list, "link", rel="amphtml").attrs["href"]
        amp_list = parse_html(output_path(self.public, amp_href))
        html_card = next(
            card for card in html_list.all("article")
            if "出典と画像を含む要約" in card.text()
        )
        amp_card = next(
            card for card in amp_list.all("article")
            if "出典と画像を含む要約" in card.text()
        )
        self.assertTrue(any(
            link.attrs.get("href") == "https://example.test/evidence/"
            for link in html_card.all("a")
        ))
        self.assertTrue(html_card.all("img"))
        self.assertTrue(html_card.all("iframe"))
        for tag in ("img", "amp-img", "iframe"):
            self.assertFalse(amp_card.all(tag))
        self.assertIn("概要では原典を参照します", amp_card.text())

        list_pages = [self.public / "posts/index.html", *self.public.glob("posts/page/*/index.html")]
        cards = [
            card for path in list_pages for card in parse_html(path).all("article")
            if "画像と検索の検証" in card.text()
        ]
        self.assertEqual(len(cards), 1)
        self.assertIn("画像の読み込みと検索結果を実機で確認", cards[0].text())

    def test_missing_optional_metadata_does_not_create_fake_urls(self) -> None:
        doc = self.doc("about/index.html", minimal=True)
        self.assertEqual(self.one(doc, "html").attrs.get("lang"), "en")
        self.assertEqual(self.one(self.doc("posts/feature/index.html"), "html").attrs.get("lang"), "ja-JP")
        self.assertIsNone(self.meta(doc, "og:image", property=True))
        self.assertIn("Plain information", self.meta(doc, "description") or "")
        web_page = self.schema(doc, "WebPage")
        self.assertEqual(web_page["author"], {"@type": "Person", "name": "Site String Author"})
        self.assertEqual(self.meta(doc, "author"), "Site String Author")
        self.assertIn("Site String Author", self.one(doc, "div", **{"class": "meta"}).text())
        self.assertNotIn("image", web_page)
        self.assertFalse(
            "0001-01-01" in (self.minimal_public / "about/index.html").read_text(encoding="utf-8"),
            "An undated fixed page rendered the zero date",
        )

    def test_multilingual_links_and_labels_match_the_actual_locale(self) -> None:
        expected = {
            "en-US": BASE_URL + "en/",
            "ja-JP": BASE_URL + "ja/",
        }
        for language, read_more in (("en", "Read more: Beta"), ("ja", "ベータの続きを読む")):
            with self.subTest(language=language):
                doc = self.doc(f"{language}/index.html", multilingual=True)
                alternates = {
                    node.attrs["hreflang"]: node.attrs["href"]
                    for node in doc.all("link") if "hreflang" in node.attrs
                }
                self.assertEqual(alternates, expected)
                self.assertEqual(self.canonical(doc), expected["en-US" if language == "en" else "ja-JP"])
                self.assertIn(read_more, [
                    node.text().strip() for node in doc.all("a")
                    if node.attrs.get("class") == "read-more"
                ])
                self.schema(doc, "WebSite")

        article = self.doc("en/posts/alpha/index.html", multilingual=True)
        article_alternates = {
            node.attrs["hreflang"]: node.attrs["href"]
            for node in article.all("link") if "hreflang" in node.attrs
        }
        self.assertEqual(article_alternates, {
            "en-US": BASE_URL + "en/posts/alpha/",
            "ja-JP": BASE_URL + "ja/posts/alpha/",
        })

    def test_paginated_multilingual_lists_share_html_canonical_with_amp(self) -> None:
        for language in ("en", "ja"):
            for section in ("", "posts/"):
                with self.subTest(language=language, section=section):
                    url = BASE_URL + f"{language}/{section}page/2/"
                    html_path = f"{language}/{section}page/2/index.html"
                    amp_candidates = {
                        f"{language}/amp/{section}page/2/index.html",
                        f"{language}/{section}amp/page/2/index.html",
                    }
                    amp_paths = [
                        path for path in amp_candidates if (self.multilingual_public / path).is_file()
                    ]
                    self.assertEqual(len(amp_paths), 1, f"Expected one AMP pager: {amp_candidates}")
                    for relative in (html_path, amp_paths[0]):
                        doc = self.doc(relative, multilingual=True)
                        self.assertEqual(self.canonical(doc), url)
                        self.assertEqual(self.meta(doc, "og:url", property=True), url)
                        self.assertFalse([node for node in doc.all("link") if "hreflang" in node.attrs])
                        self.assertEqual(self.schema(doc, "CollectionPage")["url"], url)

    def test_ugly_multilingual_pagers_match_actual_html_and_amp_next_links(self) -> None:
        public = self.multilingual_ugly_public
        for language_prefix in ("", "ja/"):
            for section in ("", "posts/"):
                with self.subTest(language=language_prefix or "en", section=section):
                    stem = language_prefix + section
                    first_candidates = (public / (stem + "index.html"), public / (stem.rstrip("/") + ".html"))
                    first_paths = [path for path in first_candidates if path.is_file()]
                    self.assertEqual(len(first_paths), 1)
                    first_html = parse_html(first_paths[0])
                    html_next = urljoin(BASE_URL, self.one(first_html, "a", **{"class": "next"}).attrs["href"])
                    second_html = parse_html(output_path(public, html_next))

                    amp_first_url = self.one(first_html, "link", rel="amphtml").attrs["href"]
                    first_amp = parse_html(output_path(public, amp_first_url))
                    amp_next = urljoin(BASE_URL, self.one(first_amp, "a", **{"class": "next"}).attrs["href"])
                    second_amp = parse_html(output_path(public, amp_next))

                    self.assertEqual(self.one(second_html, "link", rel="amphtml").attrs["href"], amp_next)
                    for doc in (second_html, second_amp):
                        self.assertEqual(self.canonical(doc), html_next)
                        self.assertEqual(self.meta(doc, "og:url", property=True), html_next)
                        self.assertEqual(self.schema(doc, "CollectionPage")["url"], html_next)


if __name__ == "__main__":
    unittest.main()
