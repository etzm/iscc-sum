# iscc-sum Tree Mode Specification

The Tree Mode option for the iscc-sum CLI creates a single ISCC checksum over the contents of an entire
directory tree.

## CLI Option Name

`--tree` or `-t`

This is short, memorable, and immediately conveys that you're treating the directory tree as a single unit.
Alternative options could be `--unified` or `--aggregate`, but `--tree` is the most intuitive.

## Checksum File Format

To indicate tree mode while staying close to existing checksum formats we use:

**Standard format:**

```
ISCC:KAD4VYCYCRWMAOV2-IAAWNVZ3NVOA5BC3DNRQCQQ6J5FUQKJMJ2Q5ORJM  ./directory/
```

**BSD-style format:**

```
ISCC (./directory/) = KAD4VYCYCRWMAOV2-IAAWNVZ3NVOA5BC3DNRQCQQ6J5FUQKJMJ2Q5ORJM
```

The key indicator is the **trailing slash** on the directory path. This convention:

- Is already used by some Unix tools to explicitly denote directories
- Is visually distinctive and easy to parse
- Doesn't require special headers or format changes
- Works with both standard and BSD output styles

## Usage Example

```bash
# Generate tree checksum
iscc-sum --tree ./my-project/ > checksums.txt

# Verify tree checksum
iscc-sum --check checksums.txt
```

The verifier would detect the trailing slash and automatically know to process the entire directory tree as a
single unit in deterministic order, rather than checking individual files.

This approach maintains compatibility with existing checksum file parsers while clearly signaling the special
tree mode through a simple, standard convention.
