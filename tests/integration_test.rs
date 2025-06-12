// Integration tests for iscc-sum

use iscc_sum::get_hello_message;

#[test]
fn test_library_hello() {
    let message = get_hello_message();
    assert_eq!(message, "hello iscc-sum");
    assert!(message.contains("iscc-sum"));
}