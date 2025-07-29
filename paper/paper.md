---
title: 'ISCC-SUM: High-Performance Content Identification for Scientific Data'
tags:
  - Python
  - Rust
  - data integrity
  - content identification
  - bioimaging
  - ISCC
  - ISO 24138
authors:
  - name: Titusz Pan
    orcid: 0000-0002-0521-4214
    affiliation: 1
  - name: Martin Etzrodt
    orcid: 0000-0003-1928-3904
    affiliation: 1
affiliations:
  - name: ISCC Foundation
    index: 1
date: 29 July 2025
bibliography: paper.bib
---

# Summary

Scientific data management faces unprecedented challenges as research instruments generate ever-larger datasets. In fields like bioimaging, where individual experiments can produce terabytes of data, traditional checksums prove inadequate for both performance and functionality. The International Standard Content Code (ISCC), standardized as ISO 24138:2024 [@iso24138:2024], offers a content-derived identification system that combines data integrity verification with similarity detection capabilities. However, existing implementations process data too slowly for practical use with large scientific datasets. ISCC-SUM addresses this performance gap through a Rust implementation [@rust2024] achieving 50-130× speedup over reference implementations, processing data at over 1 GB/s while maintaining full standard compliance.

# Statement of Need

ISCC-SUM [@pan2025isccsum] provides high-performance implementations of ISCC Data-Code and Instance-Code generation, the two fundamental components for media-agnostic content identification. The Data-Code employs content-defined chunking and MinHash algorithms to create similarity-preserving hashes, enabling researchers to identify near-duplicate datasets even when files have minor variations. The Instance-Code generates cryptographic checksums using BLAKE3 [@blake3:2020], ensuring data integrity while supporting efficient verified streaming through its tree-based structure.

This tool directly addresses requirements from the BIO-CODES project [@oscars2024biocodes], part of the European OSCARS initiative for enhancing AI-readiness of bioimaging data. Modern microscopy facilities routinely generate datasets exceeding hundreds of gigabytes, making performance critical for workflow integration. ISCC-SUM processes these files at 950-1050 MB/s, compared to 7-8 MB/s for pure Python implementations [@iscccore2024], reducing processing time from hours to minutes. The familiar checksum-style command-line interface ensures easy adoption, while Python bindings [@pyo3:2024] enable integration into existing data pipelines. Support for container formats like ZARR and HDF5, common in scientific computing, allows direct processing of complex hierarchical datasets.

Beyond bioimaging, ISCC-SUM serves diverse scientific communities requiring robust content identification. The similarity detection capability helps identify redundant submissions in data repositories, track dataset evolution across research projects, and verify exact dataset versions for computational reproducibility. By implementing the ISO 24138:2024 standard [@iso24138:2024], ISCC-SUM ensures global interoperability while introducing extensions like TREEWALK for deterministic directory hashing and wider hash formats for enhanced security. The tool's open-source nature and comprehensive test coverage (100%) provide the reliability essential for scientific infrastructure.

# Acknowledgements

This work was supported through the Open Science Clusters' Action for Research and Society (OSCARS) European project under grant agreement Nº101129751. We thank the BIO-CODES project partners at Leiden University for their collaboration in identifying requirements for bioimaging workflows.

# References