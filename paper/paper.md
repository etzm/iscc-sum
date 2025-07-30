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

To facilitate sharing and reuse scientific data management needs effective technologies to allow for identification, tracking, and integrity verification of datasets. As research instruments generate ever-larger datasets automation of these processes is essential. However traditional checksums prove inadequate for both performance and functionality. The International Standard Content Code (ISCC), standardized as ISO 24138:2024 [@iso24138:2024], offers a content-derived identification system that combines data integrity verification with similarity detection capabilities, yet existing implementations of the ISCC process data too slowly for practical use with large datasets. Here we implement a Rust version of the ISCC [@rust2024], “ISCC-SUM”, closing the performance gap and achieving 50-130× speedup over reference implementations, processing data at over 1 GB/s while maintaining full ISO 24138 standard compliance. We demonstrate that ISCC-SUM could effectively handle large bioimaging datasets with terabytes of data in size. 


# Statement of Need

Modern scientific instruments routinely generate datasets exceeding hundreds of gigabytes. A manual identification, tracking, and integrity verification of such large amounts of data is impossible, yet essential for achievement of FAIR data use[@aksenova2024data] [@chen2022fair] [@murray2021accessible] . A performant automated and standardized approach across various scientific domains with potential for easy workflow integration is lacking.

ISCC-SUM directly addresses these requirements through a high-performance implementation of ISCC Data-Code and Instance-Code generation, the two fundamental components for media-agnostic content identification. While the reference implementation of the ISCC can process 7-8 MB/s for pure Python implementations [@iscccore2024], the Rust based ISCC-SUM implementation achieved 950-1050 MB/s reducing processing time from hours to minutes.

ISCC-SUM [@pan2025isccsum]
The Data-Code employs content-defined chunking and MinHash algorithms to create similarity-preserving hashes, enabling researchers to identify near-duplicate datasets even when files have minor variations. The Instance-Code generates cryptographic checksums using BLAKE3 [@blake3:2020], ensuring data integrity while supporting efficient verified streaming through its tree-based structure. The familiar checksum-style command-line interface ensures easy adoption, while Python bindings [@pyo3:2024] enable integration into existing data pipelines. Support for container formats like ZARR and HDF5, common in scientific computing, allows direct processing of complex hierarchical datasets.

ISCC-SUM can serve diverse scientific communities requiring robust content identification. The similarity detection capability helps identify redundant submissions in data repositories, track dataset evolution across research projects, and verify exact dataset versions for computational reproducibility. By implementing the ISO 24138:2024 standard [@iso24138:2024], ISCC-SUM ensures global interoperability while introducing extensions like TREEWALK for deterministic directory hashing and wider hash formats for enhanced security. The tool's open-source nature and comprehensive test coverage (100%) provide the reliability essential for scientific infrastructure.

# Acknowledgements

This work was supported through the Open Science Clusters' Action for Research and Society (OSCARS) European project under grant agreement Nº101129751. We thank the BIO-CODES project partners at Leiden University for their collaboration in identifying requirements for bioimaging workflows.

# References