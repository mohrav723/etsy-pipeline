# Backend

This is the Python web backend for the Etsy Pipeline project.

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Architecture Overview](./docs/Architecture.md)** - System design, components, and data flow
- **[Development Guide](./docs/Development-Guide.md)** - Setup, testing, and coding patterns  
- **[Intelligent Mockup Feature](./docs/Intelligent-Mockup-Feature.md)** - AI-powered mockup generation
- **[Operations Guide](./docs/Operations-Guide.md)** - Deployment, monitoring, and troubleshooting

### Key Topics
- [Initial Setup](./docs/Development-Guide.md#setup)
- [Running Services](./docs/Development-Guide.md#running-services)
- [Testing](./docs/Development-Guide.md#testing)
- [Known Issues](./docs/Operations-Guide.md#known-issues)
- [Cost Tracking](./docs/Architecture.md#cost-tracking)

## Quick Start

1. Create a virtual environment:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Start all services:
   ```sh
   # From project root
   ./start.sh
   ```

For detailed setup instructions, see the [Development Guide](./docs/Development-Guide.md). 