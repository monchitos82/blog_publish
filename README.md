# Blog builder

This script and Jenkins pipeline are built separately from my blog source, but ideally should just be copied to it so it triggers the build and publishing process. The automation can trigger by leveraging webhooks, scheduled runs or manual triggers via Jenkins.

I am publishing this independently because I want it to be useful beyond my own blog and because my blog sources are private since I like to edit and change my project structure constantly.

To trigger the build we just need:

a) A source with all the markdown files. In this case, my blog has a simple structure:

```
myblog/
├── archive
├── assets
│   ├── index.md
│   └── style.css
├── favicon.ico
├── img
├── index.md
├── posts
│   ├── 2024
│   ├── 2024.md
│   ├── 2025
│   ├── 2025.md
│   ├── 2026
│   └── 2026.md
├── robots.txt
├── snippets
└── templates
    ├── 2024.md.j2
    ├── 2025.md.j2
    ├── 2026.md.j2
    ├── footer.html.j2
    ├── header.html.j2
    └── menu.html.j2
```

The templates (`j2`) are auto-populated with the contents of `/posts/<<year>>/` so pretty much all I have to do is write my posts as markdown and let the build script take care of the rest. Within the Python file there is a list of years, ideally, every new year we add a directory to `posts/` and a `<<year>>.md.j2` template so the new files are detected and the indexes populated.

b) The publishing process relies on Codeberg Pages, so a `pages` repository is needed.

c) There are some environment variables needed to run the script:

* `BASE_URL`      This is the Codeberg pages URL for my user
* `SRC`           This is the path to my source repository
* `DEST`          This is the path to my pages repository, defaults to "../pages"
* `YEAR`          This is the current year, defaults to the Year (yyyy) in the machine
* `YEAR_LOOKBACK` Years to look back, for my blog, it should be 2, so it builds from 2024 until 2026. Defaults to 1

These are defined in the Jenkinsfile as well, so pretty much all that I need to publish, it is controlled by these variables.