// Integration tests for directory processing features
use assert_cmd::Command;
use predicates::prelude::*;
use std::fs;
use std::path::Path;
use tempfile::TempDir;

fn create_nested_directory_structure(root: &Path) {
    // Create a nested directory structure for testing
    // root/
    //   file1.txt
    //   file2.log
    //   .hidden.txt
    //   subdir1/
    //     file3.txt
    //     file4.tmp
    //     subdir2/
    //       file5.txt
    //       file6.log
    //   tmpdir/
    //     temp1.tmp
    //     temp2.tmp

    fs::write(root.join("file1.txt"), b"content1").unwrap();
    fs::write(root.join("file2.log"), b"content2").unwrap();
    fs::write(root.join(".hidden.txt"), b"hidden content").unwrap();

    let subdir1 = root.join("subdir1");
    fs::create_dir(&subdir1).unwrap();
    fs::write(subdir1.join("file3.txt"), b"content3").unwrap();
    fs::write(subdir1.join("file4.tmp"), b"temp content").unwrap();

    let subdir2 = subdir1.join("subdir2");
    fs::create_dir(&subdir2).unwrap();
    fs::write(subdir2.join("file5.txt"), b"content5").unwrap();
    fs::write(subdir2.join("file6.log"), b"content6").unwrap();

    let tmpdir = root.join("tmpdir");
    fs::create_dir(&tmpdir).unwrap();
    fs::write(tmpdir.join("temp1.tmp"), b"temp1").unwrap();
    fs::write(tmpdir.join("temp2.tmp"), b"temp2").unwrap();
}

#[test]
fn test_recursive_default() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file3.txt"))
        .stdout(predicate::str::contains("file5.txt")); // From nested subdir2
}

#[test]
fn test_recursive_explicit() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("-r")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file3.txt"))
        .stdout(predicate::str::contains("file5.txt"));
}

#[test]
fn test_no_recursive() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--no-recursive")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file2.log"))
        .stdout(predicate::str::contains("file3.txt").not())
        .stdout(predicate::str::contains("file5.txt").not());
}

#[test]
fn test_exclude_single_pattern() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--exclude")
        .arg("*.tmp")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file4.tmp").not())
        .stdout(predicate::str::contains("temp1.tmp").not());
}

#[test]
fn test_exclude_multiple_patterns() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--exclude")
        .arg("*.tmp")
        .arg("--exclude")
        .arg("*.log")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file3.txt"))
        .stdout(predicate::str::contains("file2.log").not())
        .stdout(predicate::str::contains("file6.log").not())
        .stdout(predicate::str::contains("file4.tmp").not());
}

#[test]
fn test_exclude_directory_pattern() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--exclude")
        .arg("tmpdir/*")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("temp1.tmp").not())
        .stdout(predicate::str::contains("temp2.tmp").not());
}

#[test]
fn test_exclude_nested_pattern() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--exclude")
        .arg("*/subdir2/*")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file3.txt"))
        .stdout(predicate::str::contains("file5.txt").not())
        .stdout(predicate::str::contains("file6.log").not());
}

#[test]
fn test_max_depth_0() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--max-depth")
        .arg("0")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file2.log"))
        .stdout(predicate::str::contains("file3.txt").not());
}

#[test]
fn test_max_depth_1() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--max-depth")
        .arg("1")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file3.txt"))
        .stdout(predicate::str::contains("temp1.tmp"))
        .stdout(predicate::str::contains("file5.txt").not()); // Too deep
}

#[test]
fn test_max_depth_2() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--max-depth")
        .arg("2")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file3.txt"))
        .stdout(predicate::str::contains("file5.txt")); // Now included
}

#[test]
fn test_combined_options_no_recursive_with_exclude() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--no-recursive")
        .arg("--exclude")
        .arg("*.log")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file2.log").not())
        .stdout(predicate::str::contains("file3.txt").not()); // Not recursive
}

#[test]
fn test_combined_max_depth_with_exclude() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--max-depth")
        .arg("1")
        .arg("--exclude")
        .arg("*.tmp")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file3.txt"))
        .stdout(predicate::str::contains("file4.tmp").not()) // Excluded
        .stdout(predicate::str::contains("temp1.tmp").not()) // Excluded
        .stdout(predicate::str::contains("file5.txt").not()); // Too deep
}

#[test]
fn test_conflicting_recursive_options() {
    let temp_dir = TempDir::new().unwrap();

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("-r")
        .arg("--no-recursive")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .failure()
        .stderr(predicate::str::contains("cannot be used with"));
}

#[test]
fn test_hidden_files_included() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains(".hidden.txt"));
}

#[test]
fn test_exclude_hidden_files() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--exclude")
        .arg(".*")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains(".hidden.txt").not());
}

#[test]
fn test_deterministic_output_order() {
    let temp_dir = TempDir::new().unwrap();
    fs::write(temp_dir.path().join("z_file.txt"), b"z").unwrap();
    fs::write(temp_dir.path().join("a_file.txt"), b"a").unwrap();
    fs::write(temp_dir.path().join("m_file.txt"), b"m").unwrap();

    let mut cmd = Command::cargo_bin("isum").unwrap();
    let output = cmd.arg(temp_dir.path().to_str().unwrap()).output().unwrap();

    let stdout = String::from_utf8(output.stdout).unwrap();
    let lines: Vec<&str> = stdout.lines().collect();

    // Files should appear in sorted order
    assert!(lines[0].contains("a_file.txt"));
    assert!(lines[1].contains("m_file.txt"));
    assert!(lines[2].contains("z_file.txt"));
}

#[test]
fn test_empty_exclude_pattern() {
    let temp_dir = TempDir::new().unwrap();
    fs::write(temp_dir.path().join("test.txt"), b"test").unwrap();

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--exclude")
        .arg("") // Empty pattern should be ignored
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("test.txt"));
}

#[test]
fn test_complex_glob_pattern() {
    let temp_dir = TempDir::new().unwrap();
    create_nested_directory_structure(temp_dir.path());

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--exclude")
        .arg("**/*.tmp") // Exclude tmp files
        .arg("--exclude")
        .arg("**/*.log") // Exclude log files
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file1.txt"))
        .stdout(predicate::str::contains("file3.txt"))
        .stdout(predicate::str::contains("file5.txt"))
        .stdout(predicate::str::contains("file2.log").not())
        .stdout(predicate::str::contains("file4.tmp").not())
        .stdout(predicate::str::contains("file6.log").not())
        .stdout(predicate::str::contains("temp1.tmp").not())
        .stdout(predicate::str::contains("temp2.tmp").not());
}
