# Contributing to capa-server

Thank you for your interest in contributing! This is an independent project built on top of [capa](https://github.com/mandiant/capa).

## Getting Started

### Development Setup

1. Clone the repository
```bash
git clone <your-repo-url>
cd capa-server
```

2. Install Python dependencies
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install flare-capa
```

3. Run development server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Project Structure

```
capa-server/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── database.py      # Database models
│   ├── analyzer.py      # Capa integration
│   └── config.py        # Configuration
├── static/
│   └── index.html       # Web UI
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Areas for Contribution

### High Priority

1. **Advanced Web UI**
   - Integrate the official capa Explorer Web (Vue.js)
   - Add filtering and search capabilities
   - Implement result comparison views

2. **Authentication & Authorization**
   - Basic auth implementation
   - API key support
   - Role-based access control

3. **Database Enhancements**
   - PostgreSQL support for multi-user scenarios
   - Better indexing for large datasets
   - Result caching

4. **Analysis Features**
   - Support for analyzing URLs (fetch and analyze)
   - Batch upload interface
   - Scheduled re-analysis with updated rules

5. **Export Formats**
   - PDF report generation
   - STIX/TAXII export
   - MISP integration

### Medium Priority

1. **Testing**
   - Unit tests for API endpoints
   - Integration tests
   - Load testing

2. **Monitoring**
   - Prometheus metrics
   - Health check improvements
   - Analysis queue monitoring

3. **Documentation**
   - Architecture diagrams
   - Deployment guides
   - Video tutorials

### Nice to Have

1. **Integrations**
   - VirusTotal integration
   - Yara rule correlation
   - Sandbox automation (Cuckoo, CAPE)

2. **UI Improvements**
   - Dark mode
   - Mobile responsive design
   - Keyboard shortcuts

3. **Performance**
   - Async analysis workers
   - Result streaming for large files
   - Distributed analysis

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use type hints
- Write docstrings for all functions
- Keep functions focused and small

### Testing

Before submitting a PR:

```bash
# Test the API
curl http://localhost:8080/health

# Upload a test file
curl -X POST -F "file=@test.exe" http://localhost:8080/api/analyze
```

### Git Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test thoroughly
5. Commit with clear messages: `git commit -m "Add feature X"`
6. Push to your fork: `git push origin feature/my-feature`
7. Open a Pull Request

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Reference issues when applicable
- Keep first line under 50 characters
- Provide detailed description if needed

Example:
```
Add PostgreSQL support for production deployments

- Add SQLAlchemy engine configuration
- Update docker-compose with postgres service
- Add migration scripts
- Update documentation

Fixes #123
```

## Bug Reports

When reporting bugs, include:

1. capa-server version
2. Operating system and Docker version
3. Steps to reproduce
4. Expected behavior
5. Actual behavior
6. Logs (if applicable)

## Feature Requests

When requesting features:

1. Describe the use case
2. Explain why it's needed
3. Suggest implementation approach
4. Note any similar features in other tools

## Pull Request Process

1. Update README.md with any new features
2. Update USAGE.md if API changes
3. Add yourself to CONTRIBUTORS.md
4. Ensure Docker builds successfully
5. Test all API endpoints
6. Update version in config.py

## Questions?

Open an issue with the "question" label or reach out to maintainers.

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
