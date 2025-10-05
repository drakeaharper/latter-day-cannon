# Output Format Specification

## File Naming Convention
Format: `[Collection][Book][Chapter].md`

Examples:
- `[Old Testament][Genesis][Chapter 1].md`
- `[New Testament][Matthew][Chapter 5].md`
- `[Book of Mormon][1 Nephi][Chapter 3].md`
- `[Doctrine and Covenants][Section 1].md`
- `[Pearl of Great Price][Moses][Chapter 1].md`

## Directory Structure
```
scriptures/
├── old-testament/
│   ├── [Old Testament][Genesis][Chapter 1].md
│   ├── [Old Testament][Genesis][Chapter 2].md
│   └── ...
├── new-testament/
│   ├── [New Testament][Matthew][Chapter 1].md
│   └── ...
├── book-of-mormon/
│   ├── [Book of Mormon][1 Nephi][Chapter 1].md
│   └── ...
├── doctrine-and-covenants/
│   ├── [Doctrine and Covenants][Section 1].md
│   └── ...
└── pearl-of-great-price/
    ├── [Pearl of Great Price][Moses][Chapter 1].md
    └── ...
```

## File Content Format

### Header Information
```
Collection: Old Testament
Book: Genesis
Chapter: 1
Title: [Chapter title if available]
URL: https://www.churchofjesuschrist.org/study/scriptures/ot/gen/1?lang=eng

---
```

### Verse Format
```
1 In the beginning God created the heaven and the earth.

2 And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters.

3 And God said, Let there be light: and there was light.
```

### Complete File Example
```
Collection: Old Testament
Book: Genesis
Chapter: 1
Title: God creates the heavens and the earth
URL: https://www.churchofjesuschrist.org/study/scriptures/ot/gen/1?lang=eng

---

1 In the beginning God created the heaven and the earth.

2 And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters.

3 And God said, Let there be light: and there was light.

[... continues with all verses ...]
```

## Special Handling Notes

### Doctrine and Covenants
- Uses "Section" instead of "Chapter"
- Format: `[Doctrine and Covenants][Section 1].md`

### Book Names with Numbers
- Include the number as part of the book name
- Examples: "1 Nephi", "2 Nephi", "1 Timothy", "2 Timothy"

### Text Cleaning Rules
1. Remove study note references (superscript letters/numbers)
2. Remove clarity word markup but keep the text
3. Preserve original verse numbering
4. Maintain paragraph structure with verses
5. Remove HTML entities and convert to plain text

## Metadata for LLM Analysis
Each file will contain:
- Clear collection identification
- Book and chapter/section identification
- Source URL for verification
- Clean, numbered verse structure
- Consistent formatting for easy parsing