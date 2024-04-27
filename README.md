蘭 (Ran)
===
This theme is based on "[Jekyll Now](https://github.com/barryclark/jekyll-now)".

## Features
- Responsive design
- Support [utterances](https://utteranc.es/)

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

[params.utterances]
# https://utteranc.es/
repo = "owner/repo"
issueTerm = "pathname"
theme = "github-light"

[[menus.main]] # Enable Menu Bar
weight = 1
name = "About"
url = "/about"

[taxonomies]
tag = "tags"

[outputs]
page = ["HTML", "AMP"] # Enable AMP HTML

[markup.highlight]
codeFences = false
```

## Shortcodes

### card
Use [はてなブログカード](https://staff.hatenablog.com/entry/2014/09/05/143600)
```markdown
{{< card "https://example.com" >}}
```

### img
Basic usage
```markdown
{{< img src="example.png" h="100" w="100" >}}
```

Extended usage
```markdown
{{< img src="example.png" h="100" w="100" caption="Description" href="https://example.com" >}}
```
