# Changelog

All notable changes to the GitHub Code Research MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-02-02

### Added
- Initial release of GitHub Code Research MCP Server
- **search_patterns** tool for code search on GitHub
  - Supports language filtering
  - Automatic secret redaction
  - Configurable result limits (1-30)
  - 1-hour caching
- **get_repo_map** tool for repository mapping
  - PageRank-based symbol ranking
  - Tree-sitter AST parsing
  - Support for Python, JavaScript, TypeScript
  - 24-hour caching
  - Up to 100 files per repository
- **extract_function** tool for precise function extraction
  - Tree-sitter AST-based extraction
  - Regex fallback for unsupported languages
  - Context lines (3 before/after)
  - GitHub URL parsing
- **check_license** tool for license detection
  - GitHub License API integration
  - File-based detection fallback
  - Safety categorization (SAFE_TO_USE, VIRAL_LICENSE_WARNING, REVIEW_REQUIRED)
  - 7-day caching
- GitHub API client with automatic rate limiting
  - Two-tier rate limiting (general: 5000/hour, search: 30/minute)
  - Exponential backoff
  - Persistent rate limit state
  - Header-based rate limit updates
- Secret scanner with 14+ pattern types
  - AWS keys, GitHub tokens, API keys, JWT, private keys, etc.
  - Automatic redaction with type annotation
  - Applied to all tool outputs
- Tree-sitter parsers
  - Python parser (functions, classes, methods, imports, calls)
  - JavaScript parser (functions, arrow functions, classes, exports)
  - TypeScript parser (extends JavaScript with type support)
  - Parser factory with automatic language detection
- PageRank algorithm for symbol importance
  - NetworkX-based implementation
  - Dependency graph construction
  - Boost factors for exported symbols, entry points, classes
  - Score normalization
- File-based caching system
  - Configurable TTL per cache type
  - Pickle serialization
  - Automatic directory creation
- Configuration system
  - Multi-source: environment variables, config file, defaults
  - Pydantic validation
  - Support for .env files
- Comprehensive documentation
  - README with feature overview
  - INSTALLATION guide
  - USAGE_EXAMPLES with workflows
  - PROJECT_SUMMARY with architecture
- Test infrastructure
  - Pytest configuration
  - Test fixtures for sample code
  - Unit tests for parsers
  - Integration test stubs
- Quick start script for easy setup
- MIT License

### Security
- Automatic secret detection and redaction in all outputs
- No storage of sensitive data
- Read-only GitHub API operations
- Token validation on startup

### Performance
- Aggressive caching to minimize API calls
- Rate limit management to prevent 429 errors
- Lazy loading of parsers
- Efficient tree-sitter AST parsing

### Known Limitations
- Language support limited to Python, JavaScript, TypeScript
- Repository mapping limited to 100 files
- GitHub API rate limits apply
- Private repositories require appropriate token scopes

## [Unreleased]

### Planned Features
- Additional language parsers (Go, Rust, Java)
- GraphQL API support for better performance
- Dependency graph visualization
- Code quality metrics
- Diff analysis between commits
- PR and issue analysis tools
- Parallel file parsing
- Redis cache backend option
- Symbol search within repo maps

---

## Version History

- **0.1.0** - Initial release (February 2, 2024)
