# CLAUDE TEST REPORTER CONTEXT — CLAUDE.md

> **Inherits standards from global and workspace CLAUDE.md files with overrides below.**

## Project Context
**Purpose:** Universal test reporting engine with zero dependencies  
**Type:** Quality Assurance (Core Infrastructure)  
**Status:** Active  
**Dependencies:** All projects (for testing)

## Project-Specific Overrides

### Special Dependencies
```toml
# Test Reporter - minimal dependencies by design
jinja2 = "^3.1.0"  # For HTML template rendering
```

### Environment Variables  
```bash
# .env additions for Test Reporter
REPORTER_PORT=8002
REPORTS_DIR=/home/graham/workspace/data/test_reports
DASHBOARD_REFRESH_INTERVAL=30
FLAKY_TEST_THRESHOLD=3
RETENTION_DAYS=30
```

### Special Considerations
- **Zero Dependencies:** Designed to work without external services
- **HTML Generation:** Creates beautiful standalone reports
- **Multi-Project Dashboard:** Aggregates results across ecosystem
- **Flaky Test Detection:** ML-based detection of unreliable tests

---

## License

MIT License — see [LICENSE](LICENSE) for details.