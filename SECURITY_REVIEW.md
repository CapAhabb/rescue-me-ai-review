# Security Review Notes

This submission copy was prepared for manual review with publish-risk files
excluded.

Excluded from the review repository:

- Git metadata and other hidden dotfiles
- Local SQLite runtime database
- Python bytecode caches
- Machine-specific environment files
- Packet captures, keys, certificates, and env files if present

Secret scan terms checked included API keys, tokens, passwords, bearer headers,
private keys, database URLs, and common AI provider key names. The remaining
token references are application share-token logic and documentation examples,
not hard-coded credentials.

