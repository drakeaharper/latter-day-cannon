#!/usr/bin/env python3
"""
Create combined scripture files for NotebookLM (50 file limit)
Combines individual chapter files into larger collection files
"""

from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def combine_collection(collection_path, output_file):
    """Combine all files in a collection into one large file."""
    collection_name = collection_path.name.replace('-', ' ').title()

    logger.info(f"Combining {collection_name}...")

    # Get all markdown files and sort them
    files = sorted(collection_path.glob("*.md"))

    if not files:
        logger.warning(f"No files found in {collection_path}")
        return

    with open(output_file, 'w', encoding='utf-8') as outfile:
        # Write collection header
        outfile.write(f"# {collection_name}\n\n")
        outfile.write(f"*Combined scripture text from {len(files)} individual files*\n\n")
        outfile.write("---\n\n")

        for i, file_path in enumerate(files, 1):
            logger.info(f"  Processing {file_path.name} ({i}/{len(files)})")

            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()

                    # Add the content with a separator
                    outfile.write(content)
                    outfile.write("\n\n" + "="*80 + "\n\n")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

    logger.info(f"Created {output_file} with {len(files)} combined files")

def create_combined_files():
    """Create combined files for NotebookLM."""
    logger.info("Creating combined scripture files for NotebookLM...")

    base_dir = Path("scriptures")
    output_dir = Path("notebooklm")
    output_dir.mkdir(exist_ok=True)

    # Define collections to combine
    collections = [
        ("pearl-of-great-price", "Pearl of Great Price.md"),
        ("doctrine-and-covenants", "Doctrine and Covenants.md"),
        ("new-testament", "New Testament.md"),
        ("book-of-mormon", "Book of Mormon.md")
    ]

    # Old Testament is too large, split it into parts
    old_testament_books = {
        "01_Law": ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"],
        "02_History": ["Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
                      "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther"],
        "03_Poetry": ["Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon"],
        "04_Major_Prophets": ["Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel"],
        "05_Minor_Prophets": ["Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
                             "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi"]
    }

    # Process regular collections
    for collection_dir, output_name in collections:
        collection_path = base_dir / collection_dir
        output_file = output_dir / output_name

        if collection_path.exists():
            combine_collection(collection_path, output_file)
        else:
            logger.warning(f"Collection path not found: {collection_path}")

    # Process Old Testament in parts
    logger.info("Processing Old Testament in parts...")
    ot_path = base_dir / "old-testament"

    for part_name, book_list in old_testament_books.items():
        output_file = output_dir / f"Old Testament - {part_name.replace('_', ' ')}.md"

        with open(output_file, 'w', encoding='utf-8') as outfile:
            # Write part header
            part_title = part_name.replace('_', ' ')
            outfile.write(f"# Old Testament - {part_title}\n\n")
            outfile.write(f"*Books: {', '.join(book_list)}*\n\n")
            outfile.write("---\n\n")

            files_found = 0
            for book_name in book_list:
                # Find files for this book
                book_files = sorted(ot_path.glob(f"*{book_name}*"))

                for file_path in book_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            outfile.write(content)
                            outfile.write("\n\n" + "="*80 + "\n\n")
                            files_found += 1
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")

            logger.info(f"Created {output_file} with {files_found} files")

    # Create summary file
    summary_file = output_dir / "README.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# LDS Scriptures - NotebookLM Format\n\n")
        f.write("This folder contains combined scripture files optimized for NotebookLM's 50-file limit.\n\n")
        f.write("## Files Included:\n\n")
        f.write("1. **Pearl of Great Price.md** - Complete collection (16 chapters)\n")
        f.write("2. **Doctrine and Covenants.md** - Complete collection (138 sections)\n")
        f.write("3. **New Testament.md** - Complete collection (260 chapters)\n")
        f.write("4. **Book of Mormon.md** - Complete collection (239 chapters)\n")
        f.write("5. **Old Testament - 01 Law.md** - Genesis through Deuteronomy\n")
        f.write("6. **Old Testament - 02 History.md** - Joshua through Esther\n")
        f.write("7. **Old Testament - 03 Poetry.md** - Job through Song of Solomon\n")
        f.write("8. **Old Testament - 04 Major Prophets.md** - Isaiah through Daniel\n")
        f.write("9. **Old Testament - 05 Minor Prophets.md** - Hosea through Malachi\n\n")
        f.write("**Total: 9 files** (well under the 50-file limit)\n\n")
        f.write("Each file maintains the original structure with metadata headers and verse formatting.\n\n")
        f.write("Original individual files remain available in the `scriptures/` folder.\n")

    logger.info("Combined file creation complete!")

    # Count output files
    output_files = list(output_dir.glob("*.md"))
    logger.info(f"Created {len(output_files)} combined files in {output_dir}")

if __name__ == "__main__":
    create_combined_files()