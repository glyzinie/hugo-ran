# SEO and AI search configuration

Ran provides ordinary, crawlable HTML and consistent metadata. It is a generic
theme: authors, organizations, article claims, crawler policies, and verification
tokens belong to the site that uses it.

Google's [AI search guidance](https://developers.google.com/search/docs/appearance/ai-features)
uses the same SEO foundations as ordinary search. It does not require a special
AI schema or an additional AI text file. This theme does not generate `llms.txt`
or promise search rankings or AI citations.

## Upgrading an existing site

1. Update any template overrides alongside the theme. The shared head partials
   and metadata helpers are listed in the README.
2. Set `params.mainSections` to the sections that contain articles. These pages
   use `BlogPosting`; regular pages elsewhere use `WebPage`. Without an explicit
   setting, Hugo's main-section inference is used.
3. Check `baseURL`, including any deployment subdirectory, and rebuild the site.
   Each paginated list now has its own canonical URL. AMP uses the normal HTML
   article's canonical URL, Open Graph URL, and structured-data identifier.
4. Review visible bylines, publication dates, update dates, breadcrumbs, and
   related links. No dates or author names are invented when metadata is absent.
5. Confirm that configured logo, favicon, and thumbnail files exist. Local social
   images and favicons are emitted only when they can be resolved. Explicit
   remote URLs are used as provided; their availability is not checked at build
   time.
6. If articles used the old default archetype, an empty summary before
   `<!--more-->` now falls back to article text for metadata and list excerpts. Move the marker
   after an actual introduction when you want a manual summary on lists.

Headings keep the existing visual style. The site name is H1 only on the home
page; each article or list has its own primary heading, and article links on
lists use H2. Section and tag `_index.md` files can provide a title, description,
and visible introductory content. Tag URLs use Hugo's term permalinks.

The old automatic previous/next-page prefetch and home-page prerender are
disabled. These can consume bandwidth without improving the current page.
Site-specific measured hints can be added through `head/resource-hints.html`.

## Site metadata

```toml
baseURL = "https://example.com/"
title = "Example Journal"
defaultContentLanguage = "en"
languageCode = "en"
enableRobotsTXT = true

[params]
description = "What this site covers and who it is for."
mainSections = ["posts"]
logo = "images/logo.png"
thumbnail = "images/social.png"
thumbnailAlt = "Description of the shared social image"

[params.author]
name = "Author name"
url = "/about/"
sameAs = ["https://example.net/profile"]

# Optional: only supply an organization that actually publishes the site.
[params.publisher]
name = "Publisher name"
url = "https://example.com/"
logo = "images/logo.png"
```

The publisher is omitted when it is not configured. The site title is never
silently converted into a person's name or a publishing organization. Existing
author social handles such as `github` and `twitter` still contribute profile
links to `sameAs`.

For Japanese labels, set `defaultContentLanguage = "ja"` and
`languageCode = "ja-JP"`. Multilingual sites should configure each language in
Hugo. HTML and AMP use the current page's language, and translated pages link to
their HTML translations with `hreflang`. Paginated lists after page 1 omit
`hreflang` instead of incorrectly pointing to page 1 of another language.
Sites can add other translations in their own `i18n/` directory.

Normal HTML lists retain links and formatting in article summaries. AMP lists
use plain-text excerpts to avoid embedding HTML-only widgets in an AMP page.
Custom raw HTML in article bodies or list introductions still needs to satisfy
the chosen output format's requirements.

## Page metadata

```yaml
---
title: "A specific, descriptive article title"
date: 2026-01-10T09:00:00+09:00
publishDate: 2026-01-12T09:00:00+09:00
lastmod: 2026-02-03T14:00:00+09:00
description: "An accurate summary of this page."
thumbnail: "cover.png"
thumbnailAlt: "Description of the article image"
tags: [Hugo, Performance]
author:
  name: "Guest author"
  url: "https://example.net/about/"
toc: true
---
```

- `description` works on regular pages, the home page, sections, and terms. If
  absent, regular pages use their summary, then plain body text, then the site
  description. Generated excerpts are normalized and shortened to 160 characters;
  explicitly supplied page and site descriptions are not shortened.
- `author` on a page replaces the site author entirely. It can be a name string,
  a map with `name`, `url`, `sameAs`, and optional `type: Organization`, or `false`
  to omit that page's byline. A guest author's missing URL is not filled with
  the site author's URL.
- Publication dates use Hugo's `PublishDate` in both visible HTML and metadata.
  Updates appear only when `Lastmod` is known and later than the publication date.
  Date resolution follows the site's Hugo front matter configuration. Hugo's
  defaults can also infer a publication date from `lastmod`. To represent an
  update date without inferring a publication date, use the explicit date sources
  below. Do not change `lastmod` merely to make an unchanged article look recent.
- A page can set `schemaType` to `BlogPosting`, `Article`, `NewsArticle`,
  `WebPage`, `AboutPage`, or `ContactPage`. For example, use `AboutPage` on an
  actual author or site profile. Top-level home output uses `WebSite`, and list
  pages use `CollectionPage`. Visible breadcrumbs and `BreadcrumbList` use the
  same underlying links.
- Related links use Hugo's `related` configuration and show at most three
  matches. Configure the site's related-content indices to suit its content.

To use only explicitly supplied dates (instead of Hugo's other date fallbacks):

```toml
[frontmatter]
date = ["date"]
publishDate = ["publishDate", "date"]
lastmod = ["lastmod", "publishDate", "date"]
```

With these sources, a page with only `lastmod` displays only its update date.
Keep existing filename or Git-based date sources when the site deliberately uses
them; the theme does not override that choice.

## Images

Markdown image descriptions and titles are retained:

```markdown
![Measured response times under the stated test conditions](results.png "Test results")
```

The resolver checks a page bundle, then global `assets/`, then ordinary `static/`
files. It preserves query strings and fragments and supports a subdirectory in
`baseURL`. Available raster dimensions are included to reserve layout space.
For custom mounts or alternate static directories, mount image resources into
`assets/` so Hugo can resolve and inspect them consistently.

The first body image is eager by default; later images are lazy. A page can set
`imageLoading: lazy` or `imageLoading: eager` to override that default. Choose
based on the site's actual above-the-fold content; no image is automatically
assigned `fetchpriority="high"`.

For body images, the theme keeps the existing behavior of fetching remote image
dimensions through Hugo's resource cache. The displayed image still uses its
original URL. Explicit width and height avoid that fetch. Set
`params.remoteImageDimensions = false` at site level, or
`remoteImageDimensions: false` in a page, to disable remote dimension requests.
Social-image and favicon metadata do not initiate remote fetches.

If dimension lookup fails or is disabled, normal HTML still displays the original
image. AMP requires dimensions: when they remain unknown, Ran renders a link to
the original image instead of inventing its aspect ratio. To render such an image
in AMP without fetching dimensions, provide its actual width and height:

```toml
[markup.goldmark.parser]
wrapStandAloneImageWithinParagraph = false

[markup.goldmark.parser.attribute]
block = true
```

```markdown
![Description of the remote image](https://example.net/image.png)
{width="1200" height="800" loading="eager"}
```

Attribute-level `loading` overrides the page setting in normal HTML. Empty alt
text remains available for decorative images. State important chart findings
and values in nearby text as well as the image.

## Crawling and indexing controls

`enableRobotsTXT = true` enables Hugo's standard robots.txt. Ran does not impose a
site-wide crawler allow/deny policy, block AI training bots, or automatically
add restrictive snippet directives. A site may provide its own
`layouts/robots.txt` or `static/robots.txt`; review existing rules before changing
them. Continue using Hugo's generated sitemap and submit its deployed URL to
the relevant search consoles.

A page can opt out of indexing:

```yaml
noindex: true
```

Alternatively, `robots` accepts a string or list of directives at site or page
level. Page directives replace the site value. `noindex: true` takes precedence
over an inherited `index`. The 404 template always emits `noindex`.

```toml
[params]
robots = "max-image-preview:large"
```

This example allows larger image previews; it is optional and is not set by
the theme. `noindex` is not authentication: such pages are still public, can be
linked, and remain in Hugo's sitemap unless the site separately excludes them.
Allow crawlers to fetch a page if they need to observe its `noindex` directive.

For Google Search and its AI features, verify access for Googlebot and avoid
unintended `noindex`, `nosnippet`, or CDN/WAF challenges. For ChatGPT search,
[OpenAI documents OAI-SearchBot](https://developers.openai.com/api/docs/bots).
Its search crawling controls are independent of the GPTBot training controls.
Choose the site's policy explicitly rather than copying a universal AI-bot
block or allowance.

## Content and measurement

The default archetype leaves room for an actual introduction instead of starting
with an empty summary delimiter. Useful articles identify the answer, conditions,
method, results, limitations, sources, and relevant versions. Add only facts and
author credentials the site can support. Use natural descriptive headings and
links to relevant articles; a theme cannot supply original evidence for authors.

Validate a consuming site's generated output and deployed behavior:

1. Run the theme's regression tests as described in the README and build the site.
   Check its home page, an article, a fixed page, a tag, a paginated list, and AMP.
2. Use [Google's Rich Results Test](https://search.google.com/test/rich-results)
   for applicable structured-data features and URL Inspection in Search Console
   for indexability and Google's selected canonical.
3. Use [PageSpeed Insights](https://pagespeed.web.dev/) with representative pages
   and actual images. Measure LCP, CLS, and INP before making further loading or
   caching changes. Local markup checks are not field performance measurements.
4. Review robots.txt, HTTP status codes, CDN/WAF rules, and crawler request logs.
   Ensure missing URLs return a real HTTP 404; generating `404.html` alone does
   not configure the host's HTTP response.
5. Track search and AI referral visits in the site's analytics. Crawler access,
   indexing, visits, and citations are different signals; none guarantees another.

The optional HTML-only `head.html` partial can hold site verification tags.
Authentication, Search Console ownership, analytics consent, CDN policy, and
deployment remain responsibilities of the consuming site.
