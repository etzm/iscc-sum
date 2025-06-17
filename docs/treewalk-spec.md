# Treewalk - Storage Agnostic Deterministic Incremental Tree Traversal

> **At a Glance**: A deterministic algorithm for traversing hierarchical structures that produces consistent,
> reproducible ordering across platforms and storage types.

## Abstract

This specification defines a generic algorithm for traversing hierarchical storage structures with
deterministic ordering. While designed for file systems, the algorithm applies equally to archive formats
(ZIP, EPUB, DOCX), cloud storage (S3, Azure Blob), and any system with directory-like organization. It enables
reproducible content hashing and integrity verification by ensuring consistent traversal order regardless of
the underlying storage implementation or locale.

## Status

This specification is DRAFT as of 2025-01-17.

## 1. Introduction

### 1.1 Motivation

Content-based identifiers and integrity verification systems require deterministic file ordering to produce
consistent results across different environments. Traditional directory traversal methods yield entries in file
system-dependent order, making reproducible hashing impossible. This specification solves that problem while
enabling efficient filtering of unwanted content.

### 1.2 Scope

This specification covers:

- Deterministic ordering of hierarchical entries
- Ignore file handling for progressive filtering
- Security considerations for reference handling
- Extensibility for domain-specific filtering

It does NOT cover:

- Content reading or hashing algorithms
- Storage-specific authentication or access control
- Entry metadata beyond names and types
- Implementation details for specific storage systems

### 1.3 Notation and Conventions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",
"MAY", and "OPTIONAL" in this document are interpreted as described in [RFC 2119] and [RFC 8174].

## 2. Terminology

**Entry** : A named object within a hierarchical storage system (file, directory, archive member, S3 object).

**Container** : An entry that can contain other entries (directory, folder, ZIP archive, S3 prefix).

**NFC Normalization** : Unicode Normalization Form C - a canonical form ensuring consistent representation of
equivalent Unicode sequences.

**Ignore File** : An entry whose name starts with "." and ends with "ignore" (e.g., .gitignore, .isccignore)
containing patterns for entries to exclude.

**Reference** : A storage-specific link to another entry (symbolic link, archive member reference, S3 redirect).

## 3. Algorithm Specification

### 3.1 Entry Ordering

> 💡 **Quick Reference**: Sort entries by NFC-normalized UTF-8 encoded names

All directory entries **MUST** be sorted using the following algorithm:

1. Apply Unicode NFC normalization to each entry name
2. Encode the normalized name as UTF-8
3. Sort entries by comparing the resulting byte sequences lexicographically

#### Example

Given entries: ["café", "caffe", "Café"]

After NFC normalization and UTF-8 encoding, the sorted order is:
- "Café" (capital C sorts before lowercase)
- "café"
- "caffe"

### 3.2 Traversal Order

The algorithm **MUST** process entries in each container in this order:

1. **Ignore files first** - Entries matching pattern `.*ignore` (e.g., .gitignore)
2. **Regular entries** - All other non-container entries in sorted order
3. **Sub-containers** - Recursively in sorted order

> [!NOTE]
> This ordering ensures ignore patterns can be processed before the entries they might exclude

### 3.3 Reference Handling

The algorithm **MUST NOT** follow references when:

- Determining if an entry is a regular entry or container
- Recursing into sub-containers

References (symbolic links, redirects, etc.) **MUST** be completely excluded from traversal results.

### 3.4 Progressive Filtering

#### Basic Traversal

The simplest traversal yields all files in deterministic order without filtering.

#### Ignore File Support

When ignore file support is enabled:

1. Check for ignore files in each directory
2. Parse patterns using gitignore-style syntax
3. Accumulate patterns from root to current directory
4. Filter entries based on accumulated patterns
5. Apply patterns to both files and directories

> [!WARNING]
> Directory patterns must be checked with a trailing "/" to ensure proper matching

#### Example with .gitignore

```
repo/
├── .gitignore (contains: *.log, temp/)
├── src/
│   ├── main.py
│   └── debug.log
└── temp/
    └── cache.dat

Yields only:
- repo/.gitignore
- repo/src/main.py
```

> [!NOTE]
> The ignore file itself is included in the output (unless excluded by a parent ignore file)

## 4. Implementation Guidance

### 4.1 Storage System Adaptation

#### File Systems
- Use native directory listing APIs (e.g., `os.scandir()`)
- Filter symbolic links during initial scan
- Resolve paths to absolute form before traversal

#### Archive Formats (ZIP, EPUB, DOCX)
- Treat archive members as entries
- Use "/" as universal path separator
- Process nested archives as sub-containers
- Apply the same NFC normalization to member names

#### Cloud Storage (S3, Azure Blob)
- Use prefix-based queries for "directory" listing
- Treat key prefixes ending with "/" as containers
- Batch API calls for efficiency

### 4.2 Path Representation

- Use forward slash (/) as universal path separator
- Calculate relative paths from traversal root
- Apply NFC normalization before any path operations

### 4.3 Security Considerations

- **MUST** validate that all paths remain within the traversal root
- **MUST NOT** follow references to prevent traversal attacks
- **SHOULD** implement depth limits for deeply nested structures
- **SHOULD** enforce size limits when processing archives

## 5. Extensibility

### 5.1 Custom Ignore Files

Implementations **MAY** support different ignore file names:

- `.gitignore` - Git-style ignores
- `.npmignore` - NPM-style ignores  
- `.isccignore` - ISCC-specific ignores
- `.customignore` - Domain-specific ignores

### 5.2 Additional Filters

Implementations **MAY** add post-processing filters to exclude specific file types or patterns.

For example, an ISCC implementation might filter out metadata files:
- Files ending with `.iscc.json`
- Temporary files ending with `.tmp`
- System files like `.DS_Store` or `Thumbs.db`

## 6. Test Vectors

Implementations **MUST** produce identical ordering for these test cases:

### Test Case 1: Unicode Normalization

```
test_dir/
├── Café.txt    (NFC: C-a-f-é)
├── Café.txt    (NFD: C-a-f-e-́)
└── café.txt

Expected order:
1. test_dir/Café.txt  (capital C sorts before lowercase)
2. test_dir/café.txt
```

### Test Case 2: Ignore File Priority

```
test_dir/
├── .gitignore
├── aaa.txt
├── zzz.txt

Expected order:
1. test_dir/.gitignore  (ignore files first)
2. test_dir/aaa.txt
3. test_dir/zzz.txt
```

## 7. References

### Normative

- Unicode Standard Annex #15: Unicode Normalization Forms
- RFC 3629: UTF-8, a transformation format of ISO 10646

### Informative

- gitignore(5) - Git ignore patterns specification
- ISO 24138:2024 - International Standard Content Code
- ZIP File Format Specification
- Amazon S3 API Reference
