# Quick Start Guide

Get up and running with ISCC-SUM in minutes! This guide shows you how to install and use the command-line tool
to generate similarity-preserving ISCC checksums for files and directories.

??? info "New to Terminal/Command Line? Start Here!"

    If you've never used a terminal (also called command line) before, don't worry! Here's a quick primer:

    **What is a Terminal?**

    A terminal is a text-based way to interact with your computer. Instead of clicking buttons, you type commands.

    **How to Open a Terminal:**

    === "Windows"

        - Press ++windows+r++, type `cmd` or `powershell`, and press ++enter++
        - Or: Right-click the Start button and select "Windows Terminal" or "Command Prompt"

    === "macOS"

        - Press ++cmd+space++, type `terminal`, and press ++enter++
        - Or: Go to Applications → Utilities → Terminal

    === "Linux"

        - Press ++ctrl+alt+t++
        - Or: Look for "Terminal" in your applications menu

    **Basic Terminal Commands You'll Need:**

    - `cd foldername` - Navigate into a folder (cd = "change directory")
    - `cd ..` - Go back to the parent folder
    - `ls` (macOS/Linux) or `dir` (Windows) - List files in current folder
    - `pwd` - Show current folder path (print working directory)

    **Example Navigation:**

    ```bash
    # See where you are
    pwd

    # List files in current folder
    ls                    # macOS/Linux
    dir                   # Windows

    # Navigate to your Documents folder
    cd Documents

    # Go back one level
    cd ..
    ```

    **Tips for Beginners:**

    - :bulb: Commands are case-sensitive on macOS/Linux
    - :bulb: Press ++tab++ to auto-complete file/folder names
    - :bulb: Press ++up++ to recall previous commands
    - :bulb: Type `clear` (macOS/Linux) or `cls` (Windows) to clear the screen
    - :bulb: Copy text: ++ctrl+c++ (Windows/Linux) or ++cmd+c++ (macOS)
    - :bulb: Paste text: ++ctrl+v++ (Windows/Linux) or ++cmd+v++ (macOS)

## :rocket: Installation in 10 Seconds

The fastest way to use ISCC-SUM is with UV:

### Step 1: Install UV (One-time Setup)

UV is a modern Python tool installer that handles everything for you - including Python itself!

=== "Linux/macOS"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows"

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

!!! tip "After Installation"

    Close and reopen your terminal to ensure UV is available in your PATH.

### Step 2: Run ISCC-SUM Instantly

Now you can run ISCC-SUM without any further installation:

```bash
uvx iscc-sum myfile.txt
```

## :package: Permanent Installation

For frequent use, install ISCC-SUM globally:

```bash
uv tool install iscc-sum
```

After installation, you can simply type `iscc-sum` from anywhere in your terminal.

## :sparkles: Basic Examples

!!! question "What's an ISCC Checksum?"

    Think of it like a unique ID for your file's content. If the file changes even slightly, the fingerprint changes
    too. This helps you:

    - :mag: Detect if files have been modified
    - :gemini: Find duplicate or similar files
    - :shield: Verify file integrity

### Generate a checksum for a single file

Open your terminal in the folder containing your file, then run:

```bash
iscc-sum document.pdf
```

Output:

```
ISCC:KAATT7GQ6V5CDXEHRJPQBU3YH7V2XMCSADJWV3CZQFOPH5LOGZQQ  document.pdf
```

The long string starting with "ISCC:" is your file's unique fingerprint.

### Process multiple files

To process all JPEG images in a folder:

```bash
iscc-sum *.jpg
```

Output:

```
ISCC:KAAUSPE5KJYTY43L5OR4A5YLKQVVIMRYVFVJDVCZV5YKOEAPH3JA  image1.jpg
ISCC:KAAQZVGNJY4D2IFXEWV6DZF5JMHZ2C2ZXSOD5RCQGQEMAVVZ5VIA  image2.jpg
ISCC:KAASFWXNH6S3S7OLJQMGOQNLSCZ74CTQV3SJVHGJJ76SUXKGDZXQ  image3.jpg
```

!!! tip "Wildcard Patterns"

    The `*` symbol means "all files". So `*.jpg` means "all files ending with .jpg"

### Verify file integrity

This is useful for checking if your files have been modified or corrupted.

**Step 1: Save checksums to a file**

```bash
iscc-sum *.txt -o checksums.iscc
```

This creates a file called `checksums.iscc` containing fingerprints of all .txt files.

!!! note "Cross-platform Compatibility"

    The `-o` option ensures cross-platform compatible output (UTF-8, LF line endings), avoiding issues with shell
    redirection on Windows.

**Step 2: Later, verify the files haven't changed**

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

This tells you that `file3.txt` has been modified since you created the checksums.

## :file_folder: Tree Mode - Process Entire Directories

Sometimes you want a single fingerprint for an entire folder and all its contents. This is called "tree mode".

```bash
iscc-sum --tree ./my-project
```

!!! example "What Tree Mode Captures"

    This creates one unique fingerprint that represents:

    - :page_facing_up: All files in the folder
    - :file_folder: All subfolders and their files
    - :building_construction: The folder structure itself

!!! tip "When to use tree mode"

    - :camera: Creating a "snapshot" of a project folder
    - :mag: Checking if anything in a folder has changed
    - :package: Archiving or backing up folder structures

## :balance_scale: Comparison with Familiar Tools

If you've used `md5sum` or `sha256sum`, you'll feel right at home:

| Tool         | Generate Checksum    | Verify Files               |
| ------------ | -------------------- | -------------------------- |
| md5sum       | `md5sum file.txt`    | `md5sum -c sums.md5`       |
| sha256sum    | `sha256sum file.txt` | `sha256sum -c sums.sha256` |
| **iscc-sum** | `iscc-sum file.txt`  | `iscc-sum -c sums.iscc`    |

!!! success "Key Advantages"

    Unlike traditional checksums, ISCC-SUM:

    - :brain: Are **content-aware** - similar files produce similar codes
    - :globe_with_meridians: Follow an **ISO standard** - ensuring global interoperability
    - :zap: Process files **50-130x faster** than the ISO reference implementation

## :rocket: What's Next?

!!! abstract "Explore Further"

    - :computer: **CLI Power Users**: See the [User Guide](user-guide/) for advanced options
    - :snake: **Python Developers**: Check out the [Developer Guide](developers/) for API usage
    - :book: **Learn More**: Read about [ISCC specifications](specifications/)
