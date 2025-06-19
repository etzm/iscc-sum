# ISCC Extensions for the BioCodes Project

## Introduction

The [BioCodes project](https://tinyurl.com/yc68bd4m) addresses critical challenges in scientific data
management, particularly in the bioimaging domain where researchers work with large, complex datasets stored in
hierarchical formats. This collection of proposed extensions for the
[International Standard Content Code](https://iscc.io) (ISO 24138:2024) provides essential infrastructure for
reproducible scientific workflows, cross-platform data verification, and persistent content identification.

These specifications emerged from real-world needs in managing container formats and large-scale imaging data,
where traditional identification approaches fail due to platform-dependent file ordering, storage-agnostic
requirements, and the need for both granular and composite identification and verification. Each extension
builds upon ISO 24138:2024 to create a comprehensive solution for scientific data integrity.

## Relevance for Zarr/OME-NGFF

The bioimaging community's adoption of Zarr-based formats like OME-NGFF makes these extensions particularly
crucial. These formats store N-dimensional arrays as hierarchical directory structures containing large numbers
of chunk files, creating unique challenges for identification that our specifications address.

1. **Cross-platform Reproducibility**: Zarr hierarchies yield different traversal orders on different systems,
    breaking checksums and making verification unreliable. TreeWalk ensures identical ordering across all
    platforms and storage backends.

2. **Scalable Integrity Verification**: Large-scale OME-NGFF datasets require efficient, incremental
    checksumming. The specified APIs support progress tracking and resumable verification.

3. **Enhanced Collision Resistance**: Scientific datasets require strong guarantees against hash collisions. The
    Wide subtype's 256-bit digest provides cryptographic-strength uniqueness.

4. **Storage-Agnostic Identification**: Whether Zarr data lives in local filesystems, cloud buckets, or is
    packaged for distribution, these specifications enable consistent content identifiers.

## Proposed ISCC Extensions

### 1. TREEWALK

*Storage Agnostic Deterministic Incremental Tree Traversal*

TreeWalk solves the fundamental problem of inconsistent file ordering across platforms and storage systems. This
algorithm ensures identical traversal order whether data resides on Linux, Windows, S3, or within ZIP
archives—essential for reproducible content identification.

The specification includes:

- **TreeWalk-Base**: Core deterministic traversal algorithm
- **TreeWalk-Ignore**: Gitignore-style pattern filtering
- **TreeWalk-ISCC**: ISCC-specific pattern filtering

[Read the TreeWalk Specification →](treewalk.md)

### 2. ISCC SUBTYPE WIDE

ISCC-CODEs support various composites of individual 64-bit ISCC-UNITs. Two of those ISCC-UNITs stand out for
being media type agnostic and fully deterministic:

- **Data-Code** - A similarity-preserving hash over raw data
- **Instance-Code** - A fast checksum or cryptographic hash (blake3)

The propoposed ISCC SubType WIDE extends the composite to preserve full 128-bit digests per ISCC-UNIT, providing
enhanced collision resistance and security.

[Read the ISCC SubType WIDE Specification →](wide.md)

### 3. ISCC CHECKSUM API

A command-line interface specification that mirrors familiar tools like `md5sum` and `sha256sum`, making ISCC
adoption seamless for existing workflows. The API supports:

- Standard Unix-style checksum file formats
- Incremental verification of large datasets
- Integration with existing toolchains

[Read the CLI Checksum API Specification →](cli.md)

## Impact

Without these extensions, two researchers cannot reliably verify they have identical Zarr datasets—file listing
order varies by OS, locale, and storage backend. Standard checksums fail when the same data produces different
hashes on different systems. These specifications make reproducible computational science possible by ensuring
that content-based identifiers remain stable across all environments where scientific data is stored, processed,
and shared.

## Current Status

- **iscc-sum**: Initial High-performance reference implementation in Rust with Python bindings
- **Active Development**: Specifications and implementations are in draft status
- **Community Feedback**: Specifications and implementations are refined based on community feedback

## Future Directions

Once stabelized these specifications will eventually be submitted as official ISCC Improvement Proposals (IEPs)
at https://ieps.iscc.codes/, ensuring long-term stability and broad ecosystem support. The BioCodes project
continues to identify additional requirements from the bioimaging community that may lead to further extensions.
