// Integration tests for the isum CLI tool
use assert_cmd::Command;
use predicates::prelude::*;
use std::fs;
use tempfile::TempDir;

#[test]
fn test_help_output() {
    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--help")
        .assert()
        .success()
        .stdout(predicate::str::contains(
            "Generate ISCC Data-Code and Instance-Code checksums",
        ));
}

#[test]
fn test_version_output() {
    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--version")
        .assert()
        .success()
        .stdout(predicate::str::contains("isum"));
}

#[test]
fn test_single_file() {
    let temp_dir = TempDir::new().unwrap();
    let file_path = temp_dir.path().join("test.txt");
    fs::write(&file_path, b"hello world").unwrap();

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg(file_path.to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("ISCC:"));
}

#[test]
fn test_stdin_input() {
    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.write_stdin("hello world")
        .assert()
        .success()
        .stdout(predicate::str::contains("ISCC:"));
}

#[test]
fn test_narrow_option() {
    let temp_dir = TempDir::new().unwrap();
    let file_path = temp_dir.path().join("test.txt");
    fs::write(&file_path, b"hello world").unwrap();

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--narrow")
        .arg(file_path.to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::is_match(r"^ISCC:[A-Z0-9]{27}").unwrap());
}

#[test]
fn test_nonexistent_file() {
    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("nonexistent.txt")
        .assert()
        .failure()
        .stderr(predicate::str::contains("No such file or directory"));
}

#[test]
fn test_empty_directory() {
    let temp_dir = TempDir::new().unwrap();

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success();
}

#[test]
fn test_directory_with_files() {
    let temp_dir = TempDir::new().unwrap();
    fs::write(temp_dir.path().join("file1.txt"), b"content1").unwrap();
    fs::write(temp_dir.path().join("file2.txt"), b"content2").unwrap();

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file2.txt"));
}
