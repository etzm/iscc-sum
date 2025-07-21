// Cross-platform tests for isum CLI tool
use assert_cmd::Command;
use predicates::prelude::*;
use std::fs;
use tempfile::TempDir;

#[test]
fn test_windows_style_paths() {
    let temp_dir = TempDir::new().unwrap();
    let file_path = temp_dir.path().join("test.txt");
    fs::write(&file_path, b"test content").unwrap();

    // Test with native path separators
    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg(file_path.to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("ISCC:"));
}

#[test]
fn test_unicode_filenames() {
    let temp_dir = TempDir::new().unwrap();

    // Test various Unicode filenames
    let test_files = vec![
        "测试文件.txt",          // Chinese
        "テストファイル.txt",    // Japanese
        "тестовый_файл.txt",     // Russian
        "αρχείο_δοκιμής.txt",    // Greek
        "ملف_اختبار.txt",        // Arabic
        "fichier_testé.txt",     // French with accent
        "arquivo_teste_ção.txt", // Portuguese
    ];

    for filename in &test_files {
        let file_path = temp_dir.path().join(filename);
        fs::write(&file_path, format!("content for {filename}")).unwrap();
    }

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success();

    // Verify all files were processed
    let output = cmd.output().unwrap();
    let stdout = String::from_utf8_lossy(&output.stdout);
    for filename in &test_files {
        assert!(stdout.contains(filename), "Missing file: {filename}");
    }
}

#[test]
fn test_exclude_patterns_cross_platform() {
    let temp_dir = TempDir::new().unwrap();

    // Create a structure with both forward and backslash patterns
    let subdir = temp_dir.path().join("subdir");
    fs::create_dir(&subdir).unwrap();

    fs::write(temp_dir.path().join("keep.txt"), b"keep").unwrap();
    fs::write(temp_dir.path().join("exclude.log"), b"exclude").unwrap();
    fs::write(subdir.join("keep.txt"), b"keep sub").unwrap();
    fs::write(subdir.join("exclude.log"), b"exclude sub").unwrap();

    // Test with forward slash pattern (should work on all platforms)
    let mut cmd = Command::cargo_bin("isum").unwrap();
    let output = cmd
        .arg("--exclude")
        .arg("subdir/*.log")
        .arg(temp_dir.path().to_str().unwrap())
        .output()
        .unwrap();

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);

    // Check that we have the files we expect
    assert!(stdout.contains("keep.txt"), "Should contain root keep.txt");
    assert!(
        stdout.contains("exclude.log"),
        "Should contain root exclude.log"
    );
    assert!(
        stdout
            .lines()
            .any(|line| line.contains("subdir") && line.contains("keep.txt")),
        "Should contain subdir/keep.txt"
    );

    // Check that subdir/exclude.log was excluded
    assert!(
        !stdout
            .lines()
            .any(|line| line.contains("subdir") && line.contains("exclude.log")),
        "Should NOT contain subdir/exclude.log"
    );
}

#[test]
fn test_mixed_path_separators() {
    let temp_dir = TempDir::new().unwrap();

    // Create nested structure
    let dir1 = temp_dir.path().join("dir1");
    let dir2 = dir1.join("dir2");
    fs::create_dir_all(&dir2).unwrap();

    fs::write(dir2.join("file.txt"), b"content").unwrap();
    fs::write(dir2.join("file.tmp"), b"temp").unwrap();

    // Test exclude pattern with forward slashes (should work everywhere)
    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--exclude")
        .arg("dir1/dir2/*.tmp")
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains("file.txt"))
        .stdout(predicate::str::contains("file.tmp").not());
}

#[test]
fn test_case_sensitivity() {
    let temp_dir = TempDir::new().unwrap();

    // Create files with different cases
    fs::write(temp_dir.path().join("test.TXT"), b"upper").unwrap();
    fs::write(temp_dir.path().join("test.txt"), b"lower").unwrap();
    fs::write(temp_dir.path().join("TEST.txt"), b"all upper").unwrap();

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg("--exclude")
        .arg("*.txt") // lowercase pattern
        .arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success();

    // On Unix, only exact case matches should be excluded
    // On Windows, patterns are case-insensitive by default
    #[cfg(not(target_os = "windows"))]
    {
        let output = cmd.output().unwrap();
        let stdout = String::from_utf8_lossy(&output.stdout);
        assert!(stdout.contains("test.TXT")); // Should NOT be excluded
        assert!(!stdout.contains("test.txt")); // Should be excluded
    }
}

#[test]
fn test_special_characters_in_filenames() {
    let temp_dir = TempDir::new().unwrap();

    // Create files with special characters (avoiding those invalid on Windows)
    let special_files = vec![
        "file with spaces.txt",
        "file-with-dashes.txt",
        "file_with_underscores.txt",
        "file.multiple.dots.txt",
        "file(with)parens.txt",
        "file[with]brackets.txt",
        "file{with}braces.txt",
        "file@with@at.txt",
        "file#with#hash.txt",
        "file$with$dollar.txt",
        "file%with%percent.txt",
        "file&with&ampersand.txt",
        "file+with+plus.txt",
        "file=with=equals.txt",
        "file'with'quotes.txt",
    ];

    for filename in &special_files {
        let file_path = temp_dir.path().join(filename);
        fs::write(&file_path, format!("content: {filename}")).unwrap();
    }

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success();

    // Verify all special files were processed
    let output = cmd.output().unwrap();
    let stdout = String::from_utf8_lossy(&output.stdout);
    for filename in &special_files {
        assert!(
            stdout.contains(filename),
            "Missing special file: {filename}"
        );
    }
}

#[test]
fn test_long_paths() {
    let temp_dir = TempDir::new().unwrap();

    // Create a deeply nested directory structure
    let mut current_path = temp_dir.path().to_path_buf();
    for i in 0..10 {
        current_path = current_path.join(format!(
            "very_long_directory_name_number_{i}_that_makes_the_path_longer"
        ));
        fs::create_dir(&current_path).unwrap();
    }

    // Create a file with a long name in the deep directory
    let long_filename = "this_is_a_very_long_filename_that_should_still_work_correctly_even_with_the_deep_directory_structure.txt";
    let file_path = current_path.join(long_filename);
    fs::write(&file_path, b"content in deep file").unwrap();

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::contains(long_filename));
}

#[test]
fn test_symlinks() {
    // Skip on Windows if not running with appropriate permissions
    #[cfg(windows)]
    {
        if std::os::windows::fs::symlink_file("", "").is_err() {
            println!("Skipping symlink test - requires elevated permissions on Windows");
            return;
        }
    }

    let temp_dir = TempDir::new().unwrap();
    let target_file = temp_dir.path().join("target.txt");
    let symlink_file = temp_dir.path().join("symlink.txt");

    fs::write(&target_file, b"target content").unwrap();

    // Create symlink
    #[cfg(unix)]
    std::os::unix::fs::symlink(&target_file, &symlink_file).unwrap();

    #[cfg(windows)]
    std::os::windows::fs::symlink_file(&target_file, &symlink_file).unwrap();

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success();

    // Both files should be processed (symlinks are followed by default)
    let output = cmd.output().unwrap();
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("target.txt"));
    // Note: symlinks are followed, so symlink.txt appears as a regular file
}

#[test]
fn test_empty_directories_cross_platform() {
    let temp_dir = TempDir::new().unwrap();

    // Create several empty directories
    fs::create_dir(temp_dir.path().join("empty1")).unwrap();
    fs::create_dir(temp_dir.path().join("empty2")).unwrap();
    fs::create_dir_all(temp_dir.path().join("nested").join("empty")).unwrap();

    let mut cmd = Command::cargo_bin("isum").unwrap();
    cmd.arg(temp_dir.path().to_str().unwrap())
        .assert()
        .success()
        .stdout(predicate::str::is_empty()); // No output for empty directories
}
