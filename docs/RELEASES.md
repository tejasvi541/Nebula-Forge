# Releasing Executables (macOS, Linux, Windows)

NEBULA-FORGE includes an automated GitHub Actions release pipeline.

## What It Produces

On a version tag push (`v*`), the pipeline builds and publishes:

- macOS executable archive (`.tar.gz`)
- Linux executable archive (`.tar.gz`)
- Windows executable archive (`.zip`)

Each archive includes:

- `nebula-forge` binary (`nebula-forge.exe` on Windows)
- `README.md`

## Release Steps

1. Ensure `main` is green (CI tests passing).
2. Bump version in:
   - `pyproject.toml`
   - `nebula_forge/__init__.py`
3. Commit and push.
4. Create and push a semantic tag:

```bash
git tag v1.1.0
git push origin v1.1.0
```

1. Wait for workflow `Release Binaries` to complete.
2. Verify GitHub Release contains all three assets.

## Workflows

- CI: `.github/workflows/ci.yml`
- Release: `.github/workflows/release.yml`

## Local Build (Optional)

```bash
python -m pip install -e .
python -m pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --name nebula-forge --collect-data nebula_forge nebula_forge/__main__.py
```

Output binary appears in `dist/`.

## Troubleshooting

- Missing theme files in binary:
  - Ensure `--collect-data nebula_forge` is present in build command.
- macOS Gatekeeper warning:
  - Unsigned binaries may require manual allow in system security settings.
- Windows SmartScreen warning:
  - Unsigned binaries may show warning; this is expected without code signing.
