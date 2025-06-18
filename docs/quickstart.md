# Quick Start Guide

Get up and running with ISCC-SUM in minutes! This guide shows you how to install and use the command-line tool
to generate content fingerprints for your files.

## Installation in 10 Seconds

The fastest way to use ISCC-SUM is with `uvx` (no installation required):

```bash
uvx iscc-sum myfile.txt
```

That's it! The tool downloads automatically and runs.

## Permanent Installation

For frequent use, install ISCC-SUM globally:

```bash
# Using uv (recommended)
uv tool install iscc-sum

# Or using pip
pip install iscc-sum
```

## Basic Examples

### Generate a checksum for a single file

```bash
iscc-sum document.pdf
```

Output:

```
ISCC:KAATT7GQ6V5CDXEHRJPQBU3YH7V2XMCSADJWV3CZQFOPH5LOGZQQ  document.pdf
```

### Process multiple files

```bash
iscc-sum *.jpg
```

Output:

```
ISCC:KAAUSPE5KJYTY43L5OR4A5YLKQVVIMRYVFVJDVCZV5YKOEAPH3JA  image1.jpg
ISCC:KAAQZVGNJY4D2IFXEWV6DZF5JMHZ2C2ZXSOD5RCQGQEMAVVZ5VIA  image2.jpg
ISCC:KAASFWXNH6S3S7OLJQMGOQNLSCZ74CTQV3SJVHGJJ76SUXKGDZXQ  image3.jpg
```

### Verify file integrity

Save checksums to a file:

```bash
iscc-sum *.txt -o checksums.iscc
```

> [!NOTE]
> The `-o` option ensures cross-platform compatible output (UTF-8, LF line endings), avoiding issues with shell
> redirection on Windows.

Later, verify the files haven't changed:

```bash
iscc-sum --check checksums.iscc
```

Output:

```
file1.txt: OK
file2.txt: OK
file3.txt: FAILED
iscc-sum: WARNING: 1 computed checksum did NOT match
```

## Tree Mode - Process Entire Directories

Generate a single ISCC for an entire directory structure:

```bash
iscc-sum --tree ./my-project
```

This creates a unique fingerprint for the complete directory, perfect for:

- Versioning entire codebases
- Archiving folder structures
- Detecting changes in project directories

## Comparison with Familiar Tools

If you've used `md5sum` or `sha256sum`, you'll feel right at home:

| Tool         | Generate Checksum    | Verify Files                 |
| ------------ | -------------------- | ---------------------------- |
| md5sum       | `md5sum file.txt`    | `md5sum -c sums.md5`         |
| sha256sum    | `sha256sum file.txt` | `sha256sum -c sums.sha256`   |
| **iscc-sum** | `iscc-sum file.txt`  | `iscc-sum --check sums.iscc` |

### Key Differences

Unlike traditional checksums, ISCC codes:

- Are **content-aware** - similar files produce similar codes
- Follow an **ISO standard** - ensuring global interoperability
- Process files **50-130x faster** than the ISO reference implementation

## What's Next?

- **CLI Power Users**: See the [User Guide](user-guide.md) for advanced options
- **Python Developers**: Check out the [Developer Guide](developers/index.md) for API usage
- **Learn More**: Read about [ISCC specifications](specifications/index.md)

## Need Help?

Run `iscc-sum --help` for a complete list of options, or check our [User Guide](user-guide.md) for detailed
documentation.
