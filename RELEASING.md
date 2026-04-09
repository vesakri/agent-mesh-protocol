# How We Release

## Versioning

```
0.1.x — Patches. New features, no breaking changes. This is where we live.
0.2.0 — Only if something fundamental needs to break. We hope to never need this.
1.0.0 — Stable. Wire format locked. Multiple platforms shipping.
```

We stay in 0.1.x as long as possible. Each patch adds features without breaking existing agents.

## How to Release

1. Implement the feature, write tests
3. Update version in `pyproject.toml` and `ampro/__init__.py`
4. Add a CHANGELOG entry
5. Commit, tag, push:

```bash
git commit -m "v0.1.1 — handshake protocol, session binding, trust scoring"
git tag v0.1.1
git push origin main --tags
```

6. Verify:
```bash
pip install git+https://github.com/vesakri/agent-mesh-protocol.git@v0.1.1
python -c "import ampro; print(ampro.__version__)"
```

## Installing a Specific Version

```bash
# Latest
pip install git+https://github.com/vesakri/agent-mesh-protocol.git

# Pinned
pip install git+https://github.com/vesakri/agent-mesh-protocol.git@v0.1.1
```
