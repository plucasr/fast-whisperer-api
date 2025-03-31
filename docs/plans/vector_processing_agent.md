# Resource Processing Agent Implementation Plan

## Goal

Create a secondary AI agent that processes the 255+ cataloged theological resources (primarily Zefania XML Bibles) by downloading, parsing, converting to JSON, generating vector embeddings, and storing them in Turso's vector database for semantic search capabilities.

## Cost-Efficiency Analysis & Recommendation

### Storage Strategy Comparison

I've analyzed three approaches for storing Bible content with embeddings:

| Strategy | Rows per Bible | Embeddings per Bible | DB Size (est.) | API Calls | Search Granularity | **Recommendation** |
|----------|---------------|---------------------|----------------|-----------|-------------------|-------------------|
| **Verse-level** | ~31,000 | ~31,000 | ~500 MB | ~31,000 | Exact verse | ❌ Too expensive |
| **Chapter-level** | ~1,189 | ~1,189 | ~20 MB | ~1,189 | Full chapter | ✅ **RECOMMENDED** |
| **Multi-chapter** | ~189 | ~189 | ~5 MB | ~189 | Multiple chapters | ⚠️ Poor search quality |

### Recommended: Chapter-Level Storage

**Structure:**
```json
{
  "book": "Genesis",
  "book_number": 1,
  "chapter": 1,
  "verses": [
    {"number": 1, "text": "In the beginning..."},
    {"number": 2, "text": "And the earth was..."},
    ...
  ],
  "full_text": "In the beginning... And the earth was..." // Used for embedding
}
```

**Benefits:**
- ✅ **96% reduction** in API calls (1,189 vs 31,000)
- ✅ **96% reduction** in database rows
- ✅ Still granular enough for good search (find specific chapters)
- ✅ Can extract exact verses from JSON after retrieval
- ✅ Processes one Bible in ~10-15 minutes (vs 3-5 hours)
- ✅ Fits well within free tier: 1,500 requests/day = 1.26 Bibles/day

**Trade-offs:**
- ⚠️ Semantic search returns full chapters (not individual verses)
- ⚠️ Requires post-processing to extract specific verses
- ✅ Still excellent for most use cases (finding relevant passages)

### Cost Breakdown (Chapter-Level)

**For 1 Bible (e.g., ACF with 1,189 chapters):**
- API Calls: 1,189 embedding requests
- Processing Time: ~10-15 minutes (within free tier limits)
- Database Space: ~20 MB (including vectors)
- Free Tier Impact: Uses ~79% of daily quota

**For 10 Bibles:**
- API Calls: ~11,890 embedding requests
- Processing Time: ~8 days (staying in free tier)
- Database Space: ~200 MB total
- Cost: $0 (all free tier)

**For All 255 Resources (~100 complete Bibles):**
- API Calls: ~118,900 embedding requests
- Processing Time: ~80 days (free tier pace) OR 1 day (paid tier ~$0.50)
- Database Space: ~2 GB total
- Cost: $0 (free tier) or ~$0.50 (paid tier for speed)

## Proposed Changes

### Component 1: Database Schema Enhancement

#### [MODIFY] [db_tools.py](file:///Users/lucas/Projects/lexios/lexios-whisperer/tools/db_tools.py)

Add new tables and vector support:

**1. Bible Versions Table**
```sql
CREATE TABLE bible_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_code TEXT NOT NULL UNIQUE,  -- e.g., 'ACF', 'KJV'
    full_name TEXT NOT NULL,
    language TEXT,
    resource_id INTEGER,  -- FK to theological_resources
    total_chapters INTEGER,  -- For progress tracking
    processed_at DATETIME,
    FOREIGN KEY (resource_id) REFERENCES theological_resources(id)
)
```

**2. Bible Chapters Table with Vector Support** (Chapter-level storage)
```sql
CREATE TABLE bible_chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL,
    book_name TEXT NOT NULL,
    book_number INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,
    verses_json TEXT NOT NULL,  -- JSON array: [{"number": 1, "text": "..."}]
    full_text TEXT NOT NULL,  -- Concatenated text for embedding
    embedding F32_BLOB(768),  -- Turso native vector type (768 dimensions for Gemini)
    verse_count INTEGER,
    FOREIGN KEY (version_id) REFERENCES bible_versions(id),
    UNIQUE(version_id, book_number, chapter_number)
)
```

**3. Vector Index**
```sql
CREATE INDEX chapter_embeddings_idx ON bible_chapters(
    libsql_vector_idx(embedding)
)
```

**Example Row:**
```json
{
  "id": 1,
  "version_id": 1,
  "book_name": "John",
  "book_number": 43,
  "chapter_number": 3,
  "verses_json": "[{\"number\":1,\"text\":\"There was a man...\"},{\"number\":16,\"text\":\"For God so loved...\"}]",
  "full_text": "There was a man of the Pharisees... For God so loved the world...",
  "embedding": [0.123, 0.456, ...],  // 768-dimensional vector
  "verse_count": 36
}

---

### Component 2: XML Parser & JSON Converter

#### [NEW] [parsers/zefania_parser.py](file:///Users/lucas/Projects/lexios/lexios-whisperer/parsers/zefania_parser.py)

Create a parser for Zefania XML format:

```python
class ZefaniaParser:
    def parse_xml_to_chapters(xml_content: str) -> dict:
        """
        Parses Zefania XML and returns chapter-level structured JSON.
        
        Returns:
        {
            "version": "ACF",
            "full_name": "Almeida Corrigida Fiel",
            "language": "por",
            "chapters": [
                {
                    "book_name": "Genesis",
                    "book_number": 1,
                    "chapter_number": 1,
                    "verses": [
                        {"number": 1, "text": "No princípio..."},
                        {"number": 2, "text": "E a terra era..."}
                    ],
                    "full_text": "No princípio... E a terra era..."
                },
                ...
            ]
        }
        """
```

Features:
- Parse `<XMLBIBLE>`, `<BIBLEBOOK>`, `<CHAPTER>`, `<VERS>` elements
- Extract metadata (biblename, language)
- Flatten to chapter-level (not verse-level)
- Generate concatenated `full_text` for each chapter
- Handle XML encoding/special characters
- Validate structure

---

### Component 3: Embedding Generator

#### [NEW] [embeddings/gemini_embedder.py](file:///Users/lucas/Projects/lexios/lexios-whisperer/embeddings/gemini_embedder.py)

Generate embeddings using Google Gemini API:

```python
class GeminiEmbedder:
    def __init__(self):
        # Use text-embedding-004 model (768 dimensions, free tier available)
        
    def generate_chapter_embedding(chapter_data: dict) -> list[float]:
        """
        Generates embedding for a full chapter.
        
        Args:
            chapter_data: {
                "book_name": "John",
                "chapter_number": 3,
                "full_text": "There was a man... For God so loved..."
            }
        
        Returns:
            768-dimensional embedding vector
        """
        
    def batch_generate_embeddings(chapters: list[dict], batch_size: int = 10) -> list[list[float]]:
        """
        Batch process chapters for efficiency.
        Processes up to batch_size chapters at once.
        Returns embeddings in same order as input.
        """
```

Features:
- Rate limiting (respect free tier: 1,500 requests/day)
- Retry logic with exponential backoff
- Progress tracking with ETA
- Context-aware embeddings (include book/chapter reference in prompt)
- Batch support (process multiple chapters per API call if needed)

---

### Component 4: Processing Agent Graph

#### [NEW] [processor_agent_graph.py](file:///Users/lucas/Projects/lexios/lexios-whisperer/processor_agent_graph.py)

Create a new LangGraph agent for processing resources:

**Workflow:**
1. **Fetch Unprocessed Resources** - Query DB for `processed = 0` XML resources
2. **Download Resource** - Fetch XML file from URL
3. **Parse & Convert** - Parse Zefania XML → JSON structure
4. **Generate Embeddings** - Create vector embeddings for each verse
5. **Store in Database** - Save to `bible_versions` and `bible_verses` tables
6. **Mark as Processed** - Update `theological_resources.processed = 1`

**Nodes:**
- `fetch_unprocessed_node()` - Get next resource to process
- `download_xml_node()` - Download from URL
- `parse_xml_node()` - Parse and convert to JSON
- `embed_verses_node()` - Generate embeddings (batched)
- `store_bible_node()` - Save to database
- `mark_processed_node()` - Update status

---

### Component 5: Vector Search Tools

#### [NEW] [tools/vector_search_tools.py](file:///Users/lucas/Projects/lexios/lexios-whisperer/tools/vector_search_tools.py)

Create tools for semantic search:

```python
def search_similar_chapters(query: str, version_code: str = None, top_k: int = 5) -> list[dict]:
    """
    Semantic search for chapters similar to query.
    Uses Turso's vector_top_k() function.
    
    Returns:
    [
        {
            "book": "John",
            "chapter": 3,
            "verses": [...],  // Parsed from verses_json
            "similarity_score": 0.92
        }
    ]
    """
    
def get_verse_by_reference(version_code: str, book: str, chapter: int, verse: int) -> dict:
    """
    Exact lookup by reference.
    Retrieves chapter from DB, then extracts specific verse from JSON.
    """
    
def compare_translations(book: str, chapter: int, verse: int, versions: list[str]) -> dict:
    """
    Get same verse across multiple translations.
    Retrieves chapters for each version, extracts verse from JSON.
    """
    
def extract_verse_from_chapter(chapter_data: dict, verse_number: int) -> dict:
    """
    Helper: Extract a specific verse from chapter's verses_json.
    """
```

---

### Component 6: Updated Main Endpoint

#### [MODIFY] [main.py](file:///Users/lucas/Projects/lexios/lexios-whisperer/main.py)

Add new FastAPI endpoints:

```python
@app.post("/api/process/resource/{resource_id}")
async def process_single_resource(resource_id: int):
    """Process a single resource by ID."""
    
@app.post("/api/process/batch")
async def process_batch_resources(limit: int = 10):
    """Process multiple unprocessed resources."""
    
@app.get("/api/search/verses")
async def search_verses(query: str, version: str = None, top_k: int = 5):
    """Semantic search for verses."""
    
@app.get("/api/verse/{version}/{book}/{chapter}/{verse}")
async def get_specific_verse(version: str, book: str, chapter: int, verse: int):
    """Get specific verse by reference."""
```

---

## Verification Plan

### Automated Tests

#### Test 1: XML Parser Validation
**File**: [NEW] `tests/test_zefania_parser.py`

Download a sample Zefania XML (e.g., ACF Bible), parse it, and verify:
- Correct number of books (66 for complete Bible)
- Genesis has 50 chapters
- John 3:16 text is correctly extracted
- JSON structure matches expected schema

**Command**:
```bash
venv/bin/pytest tests/test_zefania_parser.py -v
```

#### Test 2: Embedding Generation
**File**: [NEW] `tests/test_gemini_embedder.py`

Verify:
- Embedding returns 768-dimensional vector
- Batch processing works correctly
- Rate limiting prevents API quota errors
- Context is properly included in embedding

**Command**:
```bash
venv/bin/pytest tests/test_gemini_embedder.py -v
```

#### Test 3: Database Operations
**File**: [NEW] `tests/test_vector_db.py`

Verify:
- Tables created with vector columns
- Vector index created successfully
- Insert verse with embedding works
- Vector similarity search returns results

**Command**:
```bash
venv/bin/pytest tests/test_vector_db.py -v
```

### Manual Verification

#### Verification 1: Process ACF Bible
**Steps**:
1. Run `make process-resource` to process the ACF Bible XML
2. Check database: `SELECT COUNT(*) FROM bible_verses WHERE version_id = (SELECT id FROM bible_versions WHERE version_code = 'ACF')`
3. Expected: ~31,000 verses
4. Verify embeddings are populated (not NULL)

#### Verification 2: Semantic Search Test
**Steps**:
1. Use the test script: `venv/bin/python test_vector_search.py`
2. Query: "For God so loved the world"
3. Expected: John 3:16 should be in top 3 results
4. Verify cosine similarity scores are reasonable (> 0.7)

#### Verification 3: Cross-Translation Comparison
**Steps**:
1. Ensure at least 2 Bibles are processed (e.g., ACF and KJV)
2. Query: `/api/verse/compare/John/3/16`
3. Expected: Both ACF and KJV verses returned with correct text

---

## Dependencies to Add

Update `requirements.txt`:
```
+lxml  # XML parsing
+google-generativeai  # Already included
+pytest  # For testing
+pytest-asyncio  # Async test support
```

---

## Migration Notes

- New tables are additive (won't affect existing `theological_resources`)
- `processed` flag in `theological_resources` will track completion
- Can process resources incrementally (one at a time or in batches)
- Vector indexes are automatically populated by Turso

---

## Estimated Processing Time

For 255 resources (assuming mostly complete Bibles):
- **Download**: ~1-2 minutes per Bible (depends on file size)
- **Parse**: ~5-10 seconds per Bible
- **Embed**: ~10-15 minutes per Bible (31,000 verses, rate-limited)
- **Store**: ~30-60 seconds per Bible

**Total**: ~15-20 minutes per Bible, or ~85 hours for all 255 resources if processed sequentially with free tier rate limits.

**Recommendation**: Start with 5-10 key Bibles (ACF, KJV, NIV, etc.) and expand based on usage.
