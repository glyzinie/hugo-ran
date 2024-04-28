蘭 (Ran)
===
This theme is based on "[Jekyll Now](https://github.com/barryclark/jekyll-now)".

## Features
- Responsive design
- Support: AMP HTML


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

[taxonomies]
tag = "tags"

[outputs]
page = ["HTML", "AMP"] # Enable AMP HTML

[markup.highlight]
codeFences = false
```
