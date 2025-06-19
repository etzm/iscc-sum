# Restore crates.io Publishing in Release Workflow

## Description

For the v0.1.0 release, we temporarily disabled the crates.io publishing step in the release workflow to focus on the Python package release. This issue tracks the work needed to restore Rust crate publishing for future releases.

## Background

The crates.io publishing was commented out in `.github/workflows/release.yml` in commit e08df3d on the `release-0.1.0-workflow-mods` branch.

## Tasks

- [ ] Uncomment the crates.io publishing step in `.github/workflows/release.yml`
- [ ] Remove the temporary note from `docs/releasing.md`
- [ ] Verify `CRATES_IO_TOKEN` secret is properly configured
- [ ] Test the complete release workflow including crates.io publishing

## Code to Restore

In `.github/workflows/release.yml`, uncomment:

```yaml
      - name: Publish to crates.io
        run: |
          cargo login ${{ secrets.CRATES_IO_TOKEN }}
          cargo publish --allow-dirty
        continue-on-error: true
```

## Related

- Branch: `release-0.1.0-workflow-mods`
- Documentation: `docs/releasing.md`

## Acceptance Criteria

- [ ] Future releases publish to both PyPI and crates.io
- [ ] Release workflow passes all CI checks
- [ ] Documentation reflects the restored functionality