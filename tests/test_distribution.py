# Distribution validation tests for iscc-sum

import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

import pytest

# Check if build module is available
try:
    import build  # noqa: F401

    HAS_BUILD = True
except ImportError:
    HAS_BUILD = False


@pytest.mark.slow
@pytest.mark.skipif(not HAS_BUILD, reason="build module not available")
def test_source_distribution_build():
    # type: () -> None
    """Test that source distribution can be built."""
    result = subprocess.run(
        [sys.executable, "-m", "build", "--sdist"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Build failed with stdout: {result.stdout}")
        print(f"Build failed with stderr: {result.stderr}")
    assert result.returncode == 0

    # Check that sdist was created
    dist_dir = Path("dist")
    sdist_files = list(dist_dir.glob("*.tar.gz"))
    assert len(sdist_files) >= 1

    # Verify sdist contains expected files
    sdist_path = sdist_files[0]
    with tarfile.open(sdist_path, "r:gz") as tar:
        names = tar.getnames()
        # Check for essential files
        assert any("pyproject.toml" in name for name in names)
        assert any("Cargo.toml" in name for name in names)
        assert any("src/lib.rs" in name for name in names)
        assert any("src/main.rs" in name for name in names)
        assert any("__init__.py" in name for name in names)
        assert any("py.typed" in name for name in names)


@pytest.mark.slow
@pytest.mark.skipif(not HAS_BUILD, reason="build module not available")
def test_wheel_metadata():
    # type: () -> None
    """Test that wheel contains correct metadata."""
    # Build wheel if not already built
    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Build failed with stdout: {result.stdout}")
        print(f"Build failed with stderr: {result.stderr}")
    assert result.returncode == 0

    # Find the wheel file
    dist_dir = Path("dist")
    wheel_files = list(dist_dir.glob("*.whl"))
    assert len(wheel_files) >= 1

    wheel_path = wheel_files[0]

    # Check wheel contents
    with zipfile.ZipFile(wheel_path, "r") as wheel:
        names = wheel.namelist()

        # Check for py.typed
        assert any("iscc_sum/py.typed" in name for name in names)

        # Check for compiled extension
        assert any("_core" in name and (".so" in name or ".pyd" in name) for name in names)

        # Check for metadata
        assert any("METADATA" in name for name in names)

        # Read and validate metadata
        metadata_files = [n for n in names if "METADATA" in n]
        if metadata_files:
            metadata_content = wheel.read(metadata_files[0]).decode("utf-8")
            assert "Name: iscc-sum" in metadata_content
            assert "Requires-Python:" in metadata_content


@pytest.mark.slow
@pytest.mark.skipif(not HAS_BUILD, reason="build module not available")
def test_package_installation_from_sdist():
    # type: () -> None
    """Test that package can be installed from source distribution."""
    # Build sdist
    result = subprocess.run(
        [sys.executable, "-m", "build", "--sdist"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Build failed with stdout: {result.stdout}")
        print(f"Build failed with stderr: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, result.args)

    # Find sdist file
    dist_dir = Path("dist")
    sdist_files = list(dist_dir.glob("*.tar.gz"))
    assert len(sdist_files) >= 1
    sdist_path = sdist_files[0]

    # Create temporary virtual environment
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "test_venv"

        # Create virtual environment
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
        )

        # Get python executable in venv
        if sys.platform == "win32":
            venv_python = venv_path / "Scripts" / "python.exe"
        else:
            venv_python = venv_path / "bin" / "python"

        # Install from sdist
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", str(sdist_path)],
            capture_output=True,
            text=True,
        )

        # If maturin is needed, install it first
        if result.returncode != 0 and "maturin" in result.stderr:
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "maturin"],
                check=True,
            )
            # Try again
            result = subprocess.run(
                [str(venv_python), "-m", "pip", "install", str(sdist_path)],
                capture_output=True,
                text=True,
            )

        assert result.returncode == 0

        # Test that installed package works by importing a real class
        test_result = subprocess.run(
            [str(venv_python), "-c", "import iscc_sum; assert hasattr(iscc_sum, 'DataCodeProcessor')"],
            capture_output=True,
            text=True,
        )
        assert test_result.returncode == 0


@pytest.mark.slow
def test_package_version_consistency():
    # type: () -> None
    """Test that package version is consistent across files."""
    # Read version from pyproject.toml
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists()

    # Simple version extraction (could use toml library for robustness)
    pyproject_content = pyproject_path.read_text()
    version_line = [line for line in pyproject_content.split("\n") if line.startswith("version")][0]
    pyproject_version = version_line.split("=")[1].strip().strip('"')

    # Read version from Cargo.toml
    cargo_path = Path("Cargo.toml")
    assert cargo_path.exists()

    cargo_content = cargo_path.read_text()
    version_line = [line for line in cargo_content.split("\n") if line.startswith("version")][0]
    cargo_version = version_line.split("=")[1].strip().strip('"')

    # Versions should match
    assert pyproject_version == cargo_version, (
        f"Version mismatch: pyproject.toml has {pyproject_version}, Cargo.toml has {cargo_version}"
    )
