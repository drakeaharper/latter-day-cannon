#!/usr/bin/env python3
"""
Scripture Database Builder

Populates scripture tables in mind-map.db from scraped markdown files.
Extends the existing mind map database with scripture reference data.

Usage:
    python3 build_scripture_database.py
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime
import sys


class ScriptureDatabaseBuilder:
    """Builds scripture database from markdown files"""

    # Collection definitions
    COLLECTIONS = [
        (1, "Old Testament", "OT", 1),
        (2, "New Testament", "NT", 2),
        (3, "Book of Mormon", "BofM", 3),
        (4, "Doctrine and Covenants", "D&C", 4),
        (5, "Pearl of Great Price", "PGP", 5),
        (6, "Lectures on Faith", "LoF", 6),
    ]

    # Directory name to collection ID mapping
    DIR_TO_COLLECTION = {
        "old-testament": 1,
        "new-testament": 2,
        "book-of-mormon": 3,
        "doctrine-and-covenants": 4,
        "pearl-of-great-price": 5,
        "lectures-on-faith": 6,
    }

    def __init__(self, db_path='docs/scripture-library.db', scriptures_dir='scriptures', study_helps_dir='study_helps'):
        self.db_path = Path(db_path)
        self.scriptures_dir = Path(scriptures_dir)
        self.study_helps_dir = Path(study_helps_dir)
        self.conn = None
        self.cursor = None

        # Cache for book lookups
        self.book_cache = {}

    def connect(self):
        """Connect to database"""
        print(f"Connecting to database: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print("Connected successfully")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            print("Database connection closed")

    def create_schema(self):
        """Create scripture tables"""
        print("\nCreating scripture schema...")

        schema_file = Path('schema/scripture_schema.sql')
        if not schema_file.exists():
            print(f"Error: Schema file not found: {schema_file}")
            return False

        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        # Remove comment lines first
        lines = []
        for line in schema_sql.split('\n'):
            stripped = line.strip()
            # Keep lines that aren't pure comments
            if not stripped.startswith('--'):
                lines.append(line)

        clean_sql = '\n'.join(lines)

        # Execute each statement separately (split on semicolon + newline)
        statements = re.split(r';\s*\n', clean_sql)
        for statement in statements:
            statement = statement.strip()
            if statement:
                try:
                    self.cursor.execute(statement)
                except sqlite3.Error as e:
                    print(f"Warning: {e}")
                    print(f"Statement: {statement[:100]}...")

        self.conn.commit()
        print("Schema created successfully")
        return True

    def populate_collections(self):
        """Populate scripture collections"""
        print("\nPopulating collections...")

        for id, name, abbr, sort_order in self.COLLECTIONS:
            self.cursor.execute("""
                INSERT OR IGNORE INTO scripture_collections
                (id, name, abbreviation, sort_order)
                VALUES (?, ?, ?, ?)
            """, (id, name, abbr, sort_order))

        self.conn.commit()
        print(f"Inserted {len(self.COLLECTIONS)} collections")

    def populate_books(self):
        """Populate scripture books by scanning markdown files"""
        print("\nPopulating books...")

        book_count = 0

        for collection_dir in self.scriptures_dir.iterdir():
            if not collection_dir.is_dir():
                continue

            collection_id = self.DIR_TO_COLLECTION.get(collection_dir.name)
            if collection_id is None:
                print(f"Warning: Unknown collection directory: {collection_dir.name}")
                continue

            # Get unique books from this collection
            books_found = set()

            for md_file in collection_dir.glob('*.md'):
                # Parse filename: [Collection][Book][Chapter].md
                match = re.match(r'\[.*?\]\[(.*?)\]\[.*?\]\.md', md_file.name)
                if match:
                    book_name = match.group(1)
                    books_found.add(book_name)

            # Insert books in sorted order
            for sort_order, book_name in enumerate(sorted(books_found), start=1):
                self.cursor.execute("""
                    INSERT OR IGNORE INTO scripture_books
                    (collection_id, name, abbreviation, sort_order)
                    VALUES (?, ?, ?, ?)
                """, (collection_id, book_name, None, sort_order))
                book_count += 1

        self.conn.commit()

        # Build book cache for faster lookups
        self.cursor.execute("""
            SELECT id, collection_id, name
            FROM scripture_books
        """)
        for book_id, coll_id, name in self.cursor.fetchall():
            self.book_cache[(coll_id, name)] = book_id

        print(f"Inserted {book_count} books")

    def parse_scripture_file(self, filepath):
        """Parse a scripture markdown file

        Returns:
            dict with keys: collection, book, chapter, title, url, summary, verses
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Parse metadata header
        metadata = {}
        for line in lines[:10]:
            if ':' in line and not line.startswith('---'):
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()

        # Extract summary (between --- and first verse)
        summary = []
        in_summary = False
        for line in lines:
            if line.strip() == '---':
                in_summary = not in_summary
                continue
            if in_summary:
                summary.append(line.strip())
            # Stop at first verse
            if re.match(r'^\d+\s+', line):
                break

        # Extract verses
        verses = []
        for line in lines:
            # Match lines starting with verse number
            match = re.match(r'^(\d+)\s+(.+)$', line.strip())
            if match:
                verse_num = int(match.group(1))
                verse_text = match.group(2).strip()
                verses.append((verse_num, verse_text))

        return {
            'collection': metadata.get('Collection', ''),
            'book': metadata.get('Book', ''),
            'chapter': int(metadata.get('Chapter', metadata.get('Section', '0'))),
            'title': metadata.get('Title', ''),
            'url': metadata.get('URL', ''),
            'summary': '\n'.join(summary).strip(),
            'verses': verses
        }

    def populate_chapters_and_verses(self):
        """Parse all scripture markdown files and insert into database"""
        print("\nPopulating chapters and verses...")

        chapter_count = 0
        verse_count = 0

        for collection_dir in self.scriptures_dir.iterdir():
            if not collection_dir.is_dir():
                continue

            collection_id = self.DIR_TO_COLLECTION.get(collection_dir.name)
            if collection_id is None:
                continue

            print(f"  Processing {collection_dir.name}...")

            for md_file in sorted(collection_dir.glob('*.md')):
                try:
                    # Parse file
                    data = self.parse_scripture_file(md_file)

                    # Get book_id
                    book_id = self.book_cache.get((collection_id, data['book']))
                    if not book_id:
                        print(f"    Warning: Book not found: {data['book']}")
                        continue

                    # Insert chapter
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO scripture_chapters
                        (book_id, chapter_number, title, summary, url)
                        VALUES (?, ?, ?, ?, ?)
                    """, (book_id, data['chapter'], data['title'],
                          data['summary'], data['url']))

                    chapter_id = self.cursor.lastrowid
                    chapter_count += 1

                    # Insert verses
                    for verse_num, verse_text in data['verses']:
                        self.cursor.execute("""
                            INSERT OR REPLACE INTO scripture_verses
                            (chapter_id, verse_number, text)
                            VALUES (?, ?, ?)
                        """, (chapter_id, verse_num, verse_text))
                        verse_count += 1

                    # Commit every 100 chapters
                    if chapter_count % 100 == 0:
                        self.conn.commit()
                        print(f"    Progress: {chapter_count} chapters, {verse_count} verses")

                except Exception as e:
                    print(f"    Error processing {md_file.name}: {e}")

        self.conn.commit()
        print(f"Inserted {chapter_count} chapters and {verse_count} verses")

    def populate_topical_guide(self):
        """Populate topical guide from markdown files"""
        print("\nPopulating Topical Guide...")

        tg_dir = self.study_helps_dir / 'topical_guide'
        if not tg_dir.exists():
            print(f"  Topical Guide directory not found: {tg_dir}")
            return

        topic_count = 0
        ref_count = 0

        for md_file in sorted(tg_dir.glob('*.md')):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract topic name and URL from header
                topic_match = re.search(r'^Topic:\s*(.+)$', content, re.MULTILINE)
                url_match = re.search(r'^URL:\s*(.+)$', content, re.MULTILINE)

                if not topic_match:
                    continue

                topic_name = topic_match.group(1).strip()
                url = url_match.group(1).strip() if url_match else ''

                # Insert topic
                self.cursor.execute("""
                    INSERT OR IGNORE INTO topical_guide_topics (topic_name, url)
                    VALUES (?, ?)
                """, (topic_name, url))
                topic_id = self.cursor.lastrowid
                topic_count += 1

                # Extract See Also references
                see_also_section = re.search(r'## See Also\s*\n\n(.+?)\n\n---', content, re.DOTALL)
                if see_also_section:
                    references = see_also_section.group(1).strip().split(';')
                    for ref in references:
                        ref = ref.strip()
                        if ref:
                            self.cursor.execute("""
                                INSERT INTO topical_guide_see_also (topic_id, reference)
                                VALUES (?, ?)
                            """, (topic_id, ref))

                # Extract scripture references by section
                sections = re.finditer(r'## (.+?)\n\n((?:- .+\n)+)', content)
                sort_order = 0
                for section_match in sections:
                    collection_name = section_match.group(1).strip()
                    if collection_name == 'See Also':
                        continue

                    ref_lines = section_match.group(2).strip().split('\n')
                    for line in ref_lines:
                        match = re.match(r'-\s*(.+?),\s*(.+)$', line.strip())
                        if match:
                            scripture_text = match.group(1).strip()
                            citation = match.group(2).strip()

                            self.cursor.execute("""
                                INSERT INTO topical_guide_references
                                (topic_id, collection_name, scripture_text, citation, sort_order)
                                VALUES (?, ?, ?, ?, ?)
                            """, (topic_id, collection_name, scripture_text, citation, sort_order))
                            ref_count += 1
                            sort_order += 1

                if topic_count % 100 == 0:
                    self.conn.commit()
                    print(f"    Progress: {topic_count} topics, {ref_count} references")

            except Exception as e:
                print(f"    Error processing {md_file.name}: {e}")

        self.conn.commit()
        print(f"Inserted {topic_count} topics with {ref_count} references")

    def populate_bible_dictionary(self):
        """Populate Bible Dictionary from markdown files"""
        print("\nPopulating Bible Dictionary...")

        bd_dir = self.study_helps_dir / 'bible_dictionary'
        if not bd_dir.exists():
            print(f"  Bible Dictionary directory not found: {bd_dir}")
            return

        entry_count = 0

        for md_file in sorted(bd_dir.glob('*.md')):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract entry name and URL from header
                entry_match = re.search(r'^Entry:\s*(.+)$', content, re.MULTILINE)
                url_match = re.search(r'^URL:\s*(.+)$', content, re.MULTILINE)

                if not entry_match:
                    continue

                entry_name = entry_match.group(1).strip()
                url = url_match.group(1).strip() if url_match else ''

                # Extract body (everything after ---)
                body_match = re.search(r'---\s*\n\n(.+)$', content, re.DOTALL)
                body = body_match.group(1).strip() if body_match else ''

                # Insert entry
                self.cursor.execute("""
                    INSERT OR IGNORE INTO bible_dictionary_entries
                    (entry_name, body, url)
                    VALUES (?, ?, ?)
                """, (entry_name, body, url))
                entry_count += 1

                if entry_count % 100 == 0:
                    self.conn.commit()
                    print(f"    Progress: {entry_count} entries")

            except Exception as e:
                print(f"    Error processing {md_file.name}: {e}")

        self.conn.commit()
        print(f"Inserted {entry_count} dictionary entries")

    def build_statistics(self):
        """Print database statistics"""
        print("\n" + "="*60)
        print("DATABASE STATISTICS")
        print("="*60)

        stats = [
            ("Collections", "scripture_collections"),
            ("Books", "scripture_books"),
            ("Chapters", "scripture_chapters"),
            ("Verses", "scripture_verses"),
            ("Topical Guide Topics", "topical_guide_topics"),
            ("Topical Guide References", "topical_guide_references"),
            ("Bible Dictionary Entries", "bible_dictionary_entries"),
        ]

        for label, table in stats:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            print(f"{label:.<40} {count:>8,}")

        print("="*60)

    def build(self):
        """Main build process"""
        print("="*60)
        print("SCRIPTURE DATABASE BUILDER")
        print("="*60)

        try:
            self.connect()

            # Create database if it doesn't exist
            if not self.db_path.exists():
                print(f"Creating new scripture database: {self.db_path}")

            # Create schema
            if not self.create_schema():
                return False

            # Populate data
            self.populate_collections()
            self.populate_books()
            self.populate_chapters_and_verses()
            self.populate_topical_guide()
            self.populate_bible_dictionary()

            # Show statistics
            self.build_statistics()

            print("\n✓ Scripture database build complete!")
            return True

        except Exception as e:
            print(f"\n✗ Build failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.close()


def main():
    """Main entry point"""
    builder = ScriptureDatabaseBuilder()
    success = builder.build()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
