"""Test the doctest examples in README.md"""

import doctest
import os


def test_readme_doctest():
    # type: () -> None
    """Test doctest examples in README.md."""
    # Read the README file
    readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Extract and test the pycon example

    # Test the pycon code block from README
    globs = {}
    parser = doctest.DocTestParser()

    # Find the pycon code block
    start_marker = "```pycon"
    end_marker = "```"

    start_idx = readme_content.find(start_marker)
    if start_idx != -1:
        start_idx += len(start_marker) + 1  # Skip the marker and newline
        end_idx = readme_content.find(end_marker, start_idx)
        if end_idx != -1:
            pycon_example = readme_content[start_idx:end_idx]

            # Parse and run the doctest
            test = parser.get_doctest(pycon_example, globs, "README.md", None, 0)
            runner = doctest.DocTestRunner(verbose=False)
            runner.run(test)

            # Check results
            if runner.failures > 0:
                raise AssertionError(f"Doctest failed with {runner.failures} failures")


if __name__ == "__main__":
    test_readme_doctest()
