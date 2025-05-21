# RansomMonitor

A system for automated detection of organizational exposure in ransomware campaigns

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-green.svg)
![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Basic Installation](#basic-installation)
  - [Docker Setup for Tor Collection](#docker-setup-for-tor-collection)
  - [Configuration](#configuration)
- [Usage](#usage)
  - [Starting the System](#starting-the-system)
  - [Main Menu Options](#main-menu-options)
- [Features](#features)
- [Collector Types](#collector-types)
- [Security Considerations](#security-considerations)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)
- [Contributing](#contributing)

## Overview

Ransom-Monitor is a specialized OSINT framework designed to track ransomware leak sites and alert organizations when they or their subsidiaries are mentioned. The system integrates both regular web APIs and dark web Tor-based sources to provide comprehensive coverage of ransomware actor activities.

Key features include:
- **Flexible collector architecture** supporting diverse intelligence sources
- **Effective domain matching system** with caching mechanisms for performance
- **Secure Tor integration** approach for accessing .onion sites
- **Alert generation** for matching network identifiers
- **Watchlist management** for organizations and their identifiers

## Architecture

The system consists of six primary components:

1. **Collection Framework** - Retrieves data from intelligence sources, including both regular web APIs and Tor-hosted sites
2. **Storage Layer** - Manages persistent storage of intelligence data, watchlist identifiers, and alert history
3. **Matching Engine** - Identifies potential matches between collected intelligence and watchlist identifiers
4. **Alert System** - Generates and delivers notifications about matches
5. **Tor Proxy** - Provides secure, isolated access to dark web intelligence sources
6. **User Interface** - Command-line interface with dashboard visualizations and management capabilities

## Quick Start

For those who want to get up and running quickly:

```bash
# Clone and install
git clone https://github.com/birb97/RansomMonitor
cd RansomMonitor
python -m venv venv && source venv/bin/activate

# Initialize and run
python -c "from database import DatabaseService; DatabaseService().initialize()"
python main.py
```

## Installation

### Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose (for Tor-based collection)
- Git (for obtaining the source code)
- Basic command-line familiarity
- Access to the internet, including Tor access if using dark web collection

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/birb97/RansomMonitor.git
cd RansomMonitor

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Initialize the database
python -c "from database import DatabaseService; DatabaseService().initialize()"
```

### Docker Setup for Tor Collection

The Tor collection components require Docker for secure isolation:

```bash
# Navigate to the droplet directory
cd droplet

# Build and start the containers
docker-compose build
docker-compose up -d

# Verify that the containers are running
docker ps | grep "tor-proxy\|collection-agent"

# Test the collection agent
curl http://localhost:5000/health
```

### Configuration


Example configuration:

```ini
# Edit the configuration file with your preferred settings
[General]
interval = 300
database_path = sqlite:///ransomware_intel.db

[Logging]
level = INFO
file = ransomware_intel.log

[Droplet]
endpoint = http://localhost:5000
api_secret = your-secret-key
```

## Usage

### Starting the System

```bash
# Start in foreground mode
python main.py

# Start in background mode
python main.py start-background

# Check status of background process
python main.py status

# Stop background process
python main.py stop-background
```

### Main Menu Options

1. **Start/Stop collection** - Control the collection process
2. **Manage watchlist** - Add, edit, or remove organizations and their identifiers
3. **Settings** - Configure system parameters
4. **Domain Matching Explorer** - Test and explore domain matching behavior
5. **Database Inspector** - Examine collected intelligence and alerts
6. **Check Existing Claims** - Scan historical data against the current watchlist

## Features

- **Comprehensive Coverage**: Monitors diverse ransomware intelligence sources
- **Accurate Identification**: Effectively matches organizational identifiers across different formats
- **Security Considerations**: Implements security measures when accessing potentially malicious content
- **Operational Efficiency**: Minimizes resource requirements and maintenance overhead
- **Usability**: Provides an intuitive interface for security teams
- **Extensibility**: Offers a modular architecture that can be easily extended

## Collector Types

The system supports multiple collection methods:

- **API Collectors**: Interact with structured API endpoints (e.g., Ransomlook)
- **Aggregator Collectors**: Retrieve data from web services that aggregate multiple sources (e.g., Ransomwatch, Ransomware.live)
- **Tor-Based Collectors**: Retrieve data from Tor-hosted leak sites through a secure, containerized approach

## Security Considerations

The system implements several security measures:

- **Container Isolation**: Docker containers create logical separation between the Tor processes and the main application
- **Network Namespace Isolation**: Custom internal network with no direct external access
- **Port Binding Controls**: Localhost-only binding prevents external API access
- **HMAC Authentication**: Time-limited tokens provide strong API authentication
- **Least Privilege Configuration**: Non-root user execution limits impact of potential compromise

## Development

To extend the system with new collectors or features:

1. **Adding a new collector**:
   ```python
   from collectors.base import BaseCollector
   
   class NewSourceCollector(BaseCollector):
       def __init__(self):
           super().__init__("NewSource", "https://api.newsource.com")
       
       def collect(self):
           # Implementation details
           # ...
           return processed_data
   ```

2. **Running tests**:
   ```bash
   # Run all tests
   python -m test_framework
   
   # Run specific test modules
   python -m test_framework tests.test_collectors tests.test_domain_utils
   ```

## Troubleshooting

Common issues and solutions:

- **Tor connection problems**:
  - Verify Docker containers are running: `docker ps`
  - Check Tor container logs: `docker logs tor-proxy`
  - Ensure your network allows Tor connections

- **Database errors**:
  - Verify database path in configuration
  - Check file permissions for SQLite database
  - Run database repair: `python -c "from database import DatabaseService; DatabaseService().repair()"`

- **Collection failures**:
  - Check network connectivity
  - Verify API endpoints are accessible
  - Ensure correct configuration for collection sources

## Roadmap

Future development plans:

- **Enhanced Collection Capabilities**: Discovery mechanisms for new ransomware groups and leak sites
- **Advanced Matching Algorithms**: Machine learning approaches for improved accuracy
- **Alert Prioritization System**: Confidence scoring and context-based prioritization
- **Web-Based Dashboard**: Graphical visualization of alerts, trends, and system status
- **Streamlined Installation**: Packaging options for easier deployment

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

For major changes, please open an issue first to discuss what you would like to change.

## Acknowledgments

RansomMonitor stands on the shoulders of several excellent open-source projects and services. I'd like to express my gratitude to the following:

### Core Libraries
- [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) - The SQL toolkit and Object-Relational Mapper that provides the data layer for the application
- [Requests](https://github.com/psf/requests) - The elegant HTTP library that powers the web API interactions
- [Flask](https://github.com/pallets/flask) - The lightweight WSGI web application framework used for the collection agent

### Intelligence Sources
- [Ransomlook](https://www.ransomlook.io/) - For providing structured API access to ransomware intelligence
- [Ransomware.live](https://ransomware.live/) - For their comprehensive listing of active ransomware groups
- [Ransomwatch](https://ransomwatch.telemetry.ltd/#/) - For their open-source ransomware monitoring project which inspired many others

### Security and Infrastructure
- [Tor Project](https://github.com/thetorproject) - For creating the onion routing network that enables secure access to dark web sources
- [Docker](https://github.com/docker/docker-ce) - For container technology that enables secure isolation of Tor components
- [PySocks](https://github.com/Anorov/PySocks) - For providing Python SOCKS client module for Tor communication

### Testing and Development
- [pytest](https://github.com/pytest-dev/pytest) - For the testing framework that ensures the code quality
- [Gunicorn](https://github.com/benoitc/gunicorn) - For the WSGI HTTP server that runs the collection agent

### Research and Inspiration
Special thanks to the cybersecurity research community for their work on ransomware tracking and intelligence gathering, which has influenced the project and its methodologies.

I also acknowledge all contributors who have invested time and effort in building and improving this tool.