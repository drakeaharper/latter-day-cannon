# latter-day-cannon

LDS Scripture Study Tools - Web scraping and analysis tools for LDS canonical texts and study helps.

## 🌐 Live Demo

**[View Scripture Study Helper App](https://drakeaharper.github.io/latter-day-cannon/)**

Interactive mind mapping tool for scripture study with persistent storage.

## Overview

This project scrapes and organizes all LDS canonical scriptures and study helps for analysis and interactive study:

- **Scripture Collections**: Old Testament, New Testament, Book of Mormon, Doctrine and Covenants, Pearl of Great Price (~1,584 chapters)
- **Study Helps**: Topical Guide (~3,512 topics), Bible Dictionary (~1,274 entries)
- **Web App**: Interactive mind mapping tool with SQLite WASM storage

## Features

### Scripture Scrapers
- Automated scraping of all scripture collections from churchofjesuschrist.org
- Clean markdown formatting with metadata headers
- Parallel scraping support for faster processing
- Comprehensive logging and error handling

### Web Application
- **Mind Mapping**: Visual tool for creating connections between scripture topics
- **Multiple Maps**: Save and switch between different study projects
- **Auto-save**: Automatic saving every 30 seconds
- **Offline Storage**: SQLite WASM database with localStorage persistence
- **Export/Import**: Share mind maps as JSON files

## Quick Start

### Running Scrapers

```bash
# Install dependencies
pip install requests beautifulsoup4

# Scrape all scriptures
python3 scrape_all_scriptures.py

# Scrape individual collections
python3 scrape_ot.py        # Old Testament
python3 scrape_nt.py        # New Testament
python3 scrape_bofm.py      # Book of Mormon
python3 scrape_dc.py        # Doctrine and Covenants
python3 scrape_pgp.py       # Pearl of Great Price

# Scrape study helps
python3 scrape_topical_guide.py
python3 scrape_bible_dictionary.py

# Generate combined files for NotebookLM
python3 create_combined_files.py
```

### Using the Web App

Visit the [live demo](https://drakeaharper.github.io/latter-day-cannon/) or run locally:

1. Open `docs/index.html` in a web browser
2. Navigate to the Mind Map page
3. Create nodes, connections, and save your study maps
4. All data persists in your browser's local storage

## Project Structure

```
.
├── docs/                   # Web application (GitHub Pages)
│   ├── index.html         # Home page
│   ├── pages/
│   │   └── mind-map.html  # Mind mapping tool
│   ├── js/
│   │   ├── database.js    # SQLite WASM manager
│   │   └── mind-map.js    # Mind map implementation
│   └── css/               # Styling
├── scriptures/            # Scraped scripture files
│   ├── old-testament/
│   ├── new-testament/
│   ├── book-of-mormon/
│   ├── doctrine-and-covenants/
│   └── pearl-of-great-price/
├── study_helps/           # Scraped study helps
│   ├── topical_guide/
│   └── bible_dictionary/
├── notebooklm/           # Combined files for NotebookLM
├── planning/             # Implementation documentation
└── scrape_*.py           # Scraping scripts

```

## Documentation

See [CLAUDE.md](CLAUDE.md) for detailed technical documentation including:
- Scraper architecture and implementation
- Data organization and file formats
- URL structure and API patterns
- Dependencies and configuration

## Data Format

### Scripture Files
Format: `[Collection][Book][Chapter].md`

Example: `[Old Testament][Genesis][Chapter 1].md`

### Study Help Files
Format: `[Topic/Entry Name].md`

Examples: `Baptism.md`, `Abraham.md`

## License

This project is for personal study and research purposes.

## Contributing

This is a personal scripture study project. Feel free to fork and adapt for your own use.
