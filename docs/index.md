# ISCC-SUM: High-Performance Content Identification for Science

!!! info "Version 0.1.0"

    First optimized implementation of ISCC Data-Code and Instance-Code generation.

<div class="grid cards" markdown>

- :rocket:{ .lg .middle } **50-130× Faster**

    ______________________________________________________________________

    Process large amounts of scientific data in minutes, not hours. Built with Rust for maximum performance.

- :microscope:{ .lg .middle } **Scientific Focus**

    ______________________________________________________________________

    Designed for bioimaging workflows and large-scale scientific data management.

- :shield:{ .lg .middle } **ISO Standard**

    ______________________________________________________________________

    Based on ISO 24138:2024, ensuring global interoperability.

- :wrench:{ .lg .middle } **Easy Integration**

    ______________________________________________________________________

    Drop-in replacement for checksum tools with familiar CLI and Python API.

</div>

## Solving Real Scientific Challenges

!!! success "From the BIO-CODES Project"

    ISCC-SUM addresses fundamental challenges in scientific data management, particularly for bioimaging and
    large-scale research datasets.

### :material-database: **Challenge: Large Data Volumes**

Scientific instruments generate terabytes of data daily.

**Solution:** Our Rust-based implementation processes data up to **130× faster** than the pure python ISO
reference implementation, making it practical for:

- High-throughput microscopy facilities
- Genomic sequencing centers
- Climate modeling archives
- Astronomical observation data

### :material-file-multiple: **Challenge: Complex File Formats**

Scientific data comes in hundreds of specialized formats - from DICOM medical images to HDF5 datasets.

**Solution:** ISCC-SUM focuses on improving the media-agnostic ISCC-UNITs that work with **any data format**:

=== "Container Formats"

    ```
    ✓ HDF5 (hierarchical data)
    ✓ NetCDF (climate/ocean data)
    ✓ DICOM (medical imaging)
    ✓ OME-TIFF (microscopy)
    ```

=== "Raw Data"

    ```
    ✓ FASTQ (sequencing)
    ✓ FITS (astronomy)
    ✓ SEG-Y (seismic)
    ✓ Any binary format
    ```

### :material-account-group: **Challenge: Scientific Adoption**

Researchers need tools that integrate seamlessly with existing workflows.

**Solution:** Familiar checksum-style interface:

```bash
# Just like md5sum or sha256sum
iscc-sum experiment_001.h5
ISCC:KAA7WQPPQ6J54VLNZJ4LSMDTTEMI2DDUEHCG5DQVWCJVKENQCHSTOSA  experiment_001.h5

# Process entire datasets
iscc-sum /data/microscopy/*.tiff > checksums.txt
```

## Core Components

<div class="annotate" markdown>

- **Rust Library** - High-performance implementations of Data-Code and Instance-Code algorithms (1)
- **Python Extensions** - Native bindings for seamless Python integration
- **CLI Tool** - Unix-style command familiar to every researcher
- **Single-Pass Processing** - Generate both codes reading data only once

</div>

1. Optimized for parallel processing on modern multi-core systems

## Why ISCC for Science?

!!! info "Beyond Simple Checksums"

    ISCC provides **content-derived** similarity hashes that can verify data integrity and find similar data at the
    same time.

### Unique Advantages for Research

| Feature                       | Traditional Checksums                            | ISCC-SUM                                 |
| ----------------------------- | ------------------------------------------------ | ---------------------------------------- |
| **Speed**                     | :material-speedometer-slow: Slow for large files | :material-speedometer: 50-130× faster    |
| **Data Similarity Detection** | :x: No                                           | :white_check_mark: Built-in              |
| **Container Level Checksums** | :x: No                                           | :white_check_mark: Yes, storage agnostic |
| **Standard Compliance**       | :warning: Various standards                      | :white_check_mark: ISO 24138:2024        |

## Real-World Applications

=== "Bioimaging"

    ### :microscope: Microscopy Facilities

    - **Duplicate Detection**: Identify redundant datasets across different studies
    - **Data Integrity**: Verify images haven't been corrupted during transfer
    - **Collaboration**: Share verifiable references to specific datasets

    ```python
    from iscc_sum import code_iscc_sum

    # Generate ISCC for microscopy image
    code = code_iscc_sum("cell_culture_z047.ome.tiff")
    ```

=== "Data Archives"

    ### :material-archive: Scientific Repositories

    - **Deduplication**: Save storage by identifying duplicate submissions
    - **Version Tracking**: Track dataset evolution over time
    - **Citation**: Create persistent, verifiable data citations

    ```bash
    # Process entire archive
    iscc-sum --similar /archive
    ```

=== "Computational Science"

    ### :material-chart-line: HPC Workflows

    - **Provenance**: Track inputs/outputs in complex pipelines
    - **Reproducibility**: Verify exact datasets used in publications
    - **Distribution**: Efficiently sync datasets across compute nodes

    ```bash
    # Verify dataset before processing
    iscc-sum --check dataset.iscc
    ```

## Technical Innovation

!!! example "Extending the Standard"

    ISCC-SUM introduces several enhancements beneficial for scientific computing:

<div class="grid" markdown>

:material-tree:{ .lg } **TREEWALK** : Efficient deterministic storage tree hashing for large dataset collections

:material-expand-all:{ .lg } **SUBTYPE WIDE** : Extended codes for higher precision in similarity detection

:material-api:{ .lg } **CHECKSUM API** : Drop-in replacement for existing checksum workflows

:material-web:{ .lg } **Future: WebAssembly** : Process bioimages directly in web browsers (planned)

</div>

## Performance Benchmarks

!!! success "Real-world performance of in-memory data processing"

    | Data Size | Reference | ISCC-SUM     | Speedup |
    | --------- | --------- | ------------ | ------- |
    | 1 MB      | 5.97 MB/s | 476.17 MB/s  | 79x     |
    | 10 MB     | 6.48 MB/s | 956.14 MB/   | 147×    |
    | 100 MB    | 6.09 MB/s | 1121.44 MB/s | 184×    |

## Get Started Today

<div class="grid cards" markdown>

- :material-clock-fast:{ .lg .middle } **[Quick Start](quickstart.md)**

    ______________________________________________________________________

    Install and generate your first ISCC in under 5 minutes

- :material-book-open-variant:{ .lg .middle } **[User Guide](user-guide.md)**

    ______________________________________________________________________

    Comprehensive documentation for all features

- :material-api:{ .lg .middle } **[API Reference](developers/api-reference.md)**

    ______________________________________________________________________

    Integrate ISCC-SUM into your Python applications

- :material-github:{ .lg .middle } **[GitHub](https://github.com/iscc/iscc-sum)**

    ______________________________________________________________________

    View source code and contribute

</div>

______________________________________________________________________

!!! note "About the BIO-CODES Project"

    ISCC-SUM is developed as part of BIO-CODES, funded by the European Union's Horizon Europe programme (Grant
    Agreement No 101060954). Our mission is to make advanced content identification accessible to the global
    scientific community.

[:material-information-outline: Learn more about ISCC](https://iscc.io){ .md-button .md-button--primary }
