Inconsistency in Handling Duplicate Normalized Names (Critical)

Location: Section 4.1 (Entry Ordering) vs. Section 9.1 (Test Cases 1 & 2).

Issue: Section 4.1 states: "When multiple entries have identical names after NFC normalization, implementations
MUST yield all such entries in the order they are returned by the storage system's listing API." This statement
directly contradicts the core goal of "storage agnostic deterministic" traversal. The order returned by a
storage system's API is inherently non-deterministic across different operating systems, file systems, and
locales. For example, os.listdir() in Python does not guarantee any specific order. However, Test Cases 1 and 2
in Section 9.1 show a specific, deterministic ordering for files whose names normalize to the same form (e.g.,
Café.txt and "Cafe\\u0301.txt"). The test case implies a deterministic tie-breaking rule exists, but the
specification text explicitly delegates this to a non-deterministic source.

Recommendation: The specification text in Section 4.1 MUST be changed to define a deterministic tie-breaking
rule. The most robust approach would be to use the original, non-normalized UTF-8 byte sequence as a secondary
sort key. Suggested Change (Section 4.1):

"Sort entries by lexicographically comparing their NFC-normalized, UTF-8 encoded names. If two or more names are
identical after normalization, they MUST be sorted by lexicographically comparing their original,
pre-normalization UTF-8 encoded byte sequences as a tie-breaker."
