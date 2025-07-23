#!/usr/bin/env python
"""Debug script to identify platform-specific differences in ISCC hash generation."""

import hashlib
import platform
import sys
from pathlib import Path

from iscc_sum import IsccSumProcessor
from iscc_sum.treewalk import treewalk_iscc

# Buffer size for reading files
IO_READ_SIZE = 1024 * 64  # 64KB chunks


def find_repository_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    # If no .git found, use current directory
    return Path.cwd()


def analyze_file(file_path: Path) -> dict:
    """Analyze a single file for debugging."""
    try:
        # Read file in binary mode
        with open(file_path, "rb") as f:
            content = f.read()
        
        # Calculate various hashes
        md5 = hashlib.md5(content).hexdigest()
        sha256 = hashlib.sha256(content).hexdigest()
        
        # Check for line endings
        crlf_count = content.count(b"\r\n")
        lf_count = content.count(b"\n") - crlf_count  # Don't double count
        
        # File stats
        stats = file_path.stat()
        
        return {
            "path": str(file_path),
            "size": len(content),
            "md5": md5,
            "sha256": sha256,
            "crlf_count": crlf_count,
            "lf_count": lf_count,
            "mtime": stats.st_mtime,
            "mode": oct(stats.st_mode),
        }
    except Exception as e:
        return {
            "path": str(file_path),
            "error": str(e)
        }


def main():
    """Main debug function."""
    print(f"Platform: {platform.system()} {platform.version()}")
    print(f"Python: {sys.version}")
    print("-" * 80)
    
    repo_root = find_repository_root()
    print(f"Repository root: {repo_root}")
    
    # Process files like dogfood does
    processor = IsccSumProcessor()
    file_infos = []
    total_size = 0
    
    print("\nProcessing files...")
    for file_path in treewalk_iscc(repo_root):
        file_info = analyze_file(file_path)
        if "error" not in file_info:
            # Show files with CRLF line endings
            if file_info["crlf_count"] > 0:
                print(f"CRLF file: {file_info['path']} ({file_info['crlf_count']} CRLF, {file_info['lf_count']} LF)")
            
            # Process file for ISCC
            try:
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(IO_READ_SIZE)
                        if not chunk:
                            break
                        processor.update(chunk)
                total_size += file_info["size"]
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        file_infos.append(file_info)
    
    # Get ISCC result
    result = processor.result(wide=True, add_units=True)
    
    print(f"\nProcessed {len(file_infos)} files, total size: {total_size:,} bytes")
    print(f"ISCC: {result['iscc']}")
    print(f"Data hash: {result['datahash']}")
    print(f"Units: {result['units']}")
    
    # Find suspicious files
    print("\nFiles with mixed line endings:")
    for info in file_infos:
        if "error" not in info and info["crlf_count"] > 0 and info["lf_count"] > 0:
            print(f"  {info['path']}: {info['crlf_count']} CRLF, {info['lf_count']} LF")
    
    # Save detailed output
    output_file = repo_root / "debug_output.txt"
    with open(output_file, "w", newline="\n") as f:
        f.write(f"Platform: {platform.system()} {platform.version()}\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"ISCC: {result['iscc']}\n")
        f.write(f"Data hash: {result['datahash']}\n")
        f.write(f"Total files: {len(file_infos)}\n")
        f.write(f"Total size: {total_size}\n")
        f.write("\nFile details:\n")
        for info in sorted(file_infos, key=lambda x: x.get("path", "")):
            if "error" not in info:
                f.write(f"{info['path']}: size={info['size']}, md5={info['md5']}, crlf={info['crlf_count']}, lf={info['lf_count']}\n")
    
    print(f"\nDetailed output saved to: {output_file}")


if __name__ == "__main__":
    main()