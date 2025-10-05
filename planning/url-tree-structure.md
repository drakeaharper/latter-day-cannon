# Scripture Website URL Tree Structure

## Base URL Pattern
`https://www.churchofjesuschrist.org/study/scriptures`

## Collection Level Structure

### 1. Scripture Collections
- **Old Testament**: `/study/scriptures/ot?lang=eng`
- **New Testament**: `/study/scriptures/nt?lang=eng`
- **Book of Mormon**: `/study/scriptures/bofm?lang=eng`
- **Doctrine and Covenants**: `/study/scriptures/dc-testament?lang=eng`
- **Pearl of Great Price**: `/study/scriptures/pgp?lang=eng`

### 2. Book Level Structure
Pattern: `/study/scriptures/{collection}/{book-abbreviation}?lang=eng`

Examples:
- Genesis: `/study/scriptures/ot/gen?lang=eng`
- Matthew: `/study/scriptures/nt/matt?lang=eng`
- 1 Nephi: `/study/scriptures/bofm/1-ne?lang=eng`

### 3. Chapter Level Structure
Pattern: `/study/scriptures/{collection}/{book-abbreviation}/{chapter-number}?lang=eng`

Examples:
- Genesis Chapter 1: `/study/scriptures/ot/gen/1?lang=eng`
- Matthew Chapter 5: `/study/scriptures/nt/matt/5?lang=eng`
- 1 Nephi Chapter 3: `/study/scriptures/bofm/1-ne/3?lang=eng`

## HTML Structure for Content Extraction

### Chapter Content
```html
<div class="body-block">
  <p class="verse">
    <span class="verse-number">1</span>
    Verse text content...
  </p>
</div>
```

### Navigation Elements
- Book listing: `<nav class="toc">` with `<a class="list-tile">` links
- Chapter listing: Sequential numbered links in table of contents

## Key Identifiers for Scraping
- Verse content: `<p class="verse">`
- Verse numbers: `<span class="verse-number">`
- Navigation links: `<a class="list-tile">`
- Study notes: `<a class="study-note-ref">`
- Clarity words: `<span class="clarity-word">`

## Collection Abbreviations
- **ot**: Old Testament
- **nt**: New Testament
- **bofm**: Book of Mormon
- **dc-testament**: Doctrine and Covenants
- **pgp**: Pearl of Great Price

## Required Parameters
- `lang=eng`: Language specification (English)
- `platform=web`: Platform specification (when accessing main page)