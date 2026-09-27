蘭 (Ran)
===
This theme is based on "[Jekyll Now](https://github.com/barryclark/jekyll-now)".

## Features
- Responsive design
- AMP HTML

## Requirements

Hugo **0.146.0 or later** and [Dart Sass](https://gohugo.io/functions/css/sass/#dart-sass),
with the `sass` executable available on `PATH` in both local and CI environments.
The theme uses Dart Sass to compile its SCSS for both HTML and AMP output.

Shared colors and responsive breakpoints are defined in `assets/_tokens.scss`.

## Template overrides

This theme uses Hugo's [template system introduced in v0.146.0](https://gohugo.io/templates/new-templatesystem-overview/).
When upgrading a site with custom layouts, update its overrides to match:

| Previous location | New location |
| --- | --- |
| `layouts/_default/baseof.html` | `layouts/baseof.html` |
| `layouts/_default/single.html` | `layouts/page.html` |
| `layouts/_default/list.html` | `layouts/list.html` |
| `layouts/_default/tag.terms.html` | `layouts/tags/taxonomy.html` |
| `layouts/_default/_markup/` | `layouts/_markup/` |
| `layouts/partials/` | `layouts/_partials/` |
| `layouts/shortcodes/` | `layouts/_shortcodes/` |

Apply the same moves to `.amp.html` variants. The metadata helpers in
`layouts/_partials/templates/` return strings and are called with `partial`,
for example `{{ partial "templates/title.html" . }}`, instead of global named templates.

HTML and AMP share `head/metadata.html`, `head/resource-hints.html`, `header.html`,
`footer.html`, and `article.html` under `layouts/_partials/`. The header and article
partials receive a dictionary with `page` (the current page) and `isAMP` (a boolean);
the other shared partials receive the current page directly. Existing metadata,
JSON-LD, social-link, and comment partials keep their page context when overridden.
Format-specific scripts and styles remain in the respective base templates.

### Compatibility notes

- In Hugo 0.166.0, the AMP-only `gist`, `twitter`, and `youtube` shortcode
  templates are also selected for HTML output. This also occurs with the
  previous layout structure. Sites using these embeds on that version need
  explicit HTML shortcode templates as well.
- Hugo 0.166.0 emits a deprecation warning for `.Site.LanguageCode`. The theme
  retains this API because its replacement, `.Site.Language.Locale`, is not
  available in Hugo 0.146.0.

## `hugo.toml` example
```toml
theme = "ran"

baseurl = "https://example.com/"
title = "SiteTitle"

[params]
description = "Description"
favicon = "img/favicon.png"
logo = "img/logo.png"
thumbnail = "img/thumb.png"

[params.author]
name = "Your Name"
url = "Your Web SITE URL"
email = "your@example.com"
twitter = ""
github = ""
stackoverflow = ""
linkedin = ""
facebook = ""
instagram = ""
pinterest = ""
tumblr = ""
youtube = ""

[[menus.main]] # Enable Menu Bar
weight = 1
name = "About"
url = "/about"

[[menus.main]]
url = "/tags/"
name = "Tag"

[taxonomies]
tag = "tags"

[outputs]
page = ["HTML", "AMP"] # Enable AMP HTML

[markup.highlight]
codeFences = false
```
