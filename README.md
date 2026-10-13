# Vaibhav Lalwani — academic website

A fast, chic, professional academic website built with [Quarto](https://quarto.org).
The **Research and Publications** page refreshes automatically every quarter from
[OpenAlex](https://openalex.org) using your ORCID, while every page remains plain
Markdown that you can edit by hand at any time.

Live site target: **https://www.vaibhavfin.com**

---

## What's here

| Path | Purpose |
|---|---|
| `_quarto.yml` | Site title, navigation, footer, theme |
| `index.qmd` | **Bio** page (home) |
| `teaching.qmd` | **Teaching** page |
| `research.qmd` | **Research and Publications** page (auto-filled) |
| `data-code.qmd` | **Data and Code** page |
| `styles.css` | Colours, fonts, and layout — edit freely |
| `_includes/head.html` | Fonts and `<head>` additions |
| `scripts/update_publications.py` | Pulls your works from OpenAlex |
| `scripts/settings.toml` | ORCID, manual links, and notes |
| `_publications.md`, `_metrics.md`, `publications.bib` | **Auto-generated — do not edit by hand** |
| `.github/workflows/publish.yml` | Quarterly update + deploy |

## Local preview

1. Install Quarto: <https://quarto.org/docs/get-started/>
2. Install Python 3.11+ (already required only for the update script).
3. Generate the publication list (optional — a copy is committed):

   ```bash
   python scripts/update_publications.py
   ```

4. Preview the site live:

   ```bash
   quarto preview
   ```

5. Build the static site into `_site/`:

   ```bash
   quarto render
   ```

## How the automatic update works

- `.github/workflows/publish.yml` runs on the 1st of January, April, July and
  October (and on every push, and on demand from the **Actions** tab).
- The script queries OpenAlex for `orcid = "0000-0001-7476-5311"`, splits the
  results into **peer-reviewed publications** and **working papers**, and writes
  `_publications.md`, `_metrics.md` and `publications.bib`.
- If anything changed, the bot commits it, then Quarto rebuilds and publishes to
  the `gh-pages` branch.
- Nothing is scraped from Google Scholar (which has no API and forbids scraping);
  Google Scholar stays linked in the navigation bar as a profile.

## Making manual edits

**Everyday edits** (bio text, teaching courses, data/code links): open the matching
`.qmd` file and edit the Markdown. Commit and push — the site updates.

**Tweaks to the auto-generated list** — edit `scripts/settings.toml`, never
`_publications.md`:

- Hide a duplicate or unwanted entry:

  ```toml
  exclude_ids = ["W7134948737"]
  ```

- Add a PDF, code, dataset or slide link to a paper (use the OpenAlex id shown in
  the URL of its entry, e.g. `W7213254616`):

  ```toml
  [links.W7213254616]
  pdf = "https://example.org/paper.pdf"
  code = "https://github.com/you/repo"
  ```

- Add a note under a paper:

  ```toml
  [notes]
  W7213254616 = "Forthcoming."
  ```

Then re-run `python scripts/update_publications.py`.

## Replacing the photo

Put your photo in `assets/` (e.g. `assets/profile.jpg`) and update the `<img>` in
`index.qmd` to point at it. The current `assets/profile.svg` is a placeholder.

## Deploying to www.vaibhavfin.com

1. Create a GitHub repository and push this folder to the `main` branch.
2. In **Settings → Pages**, set **Source** to the `gh-pages` branch.
3. Push once (or run the workflow) so the `gh-pages` branch is created.
4. The custom domain `www.vaibhavfin.com` is already set on the repo
   (**Settings → Pages**). Point your DNS at GitHub Pages at the provider where
   `vaibhavfin.com` is managed:

   | Type | Name | Value |
   |---|---|---|
   | CNAME | `www` | `vaibhavlalwani.github.io` |
   | A | `@` (apex `vaibhavfin.com`) | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |

   Then remove the Google Sites custom-domain mapping for `www.vaibhavfin.com`,
   and once DNS resolves tick **Enforce HTTPS** in **Settings → Pages**.
5. Once the new site is live, you can retire the Google Sites version.

## Changing colours / fonts

Everything is in `styles.css` under `:root` (`--navy`, `--accent`, `--muted`, …)
and in `_includes/head.html` for the Google Fonts.
