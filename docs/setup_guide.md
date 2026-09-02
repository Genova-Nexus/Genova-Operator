# Setup Guide — Genova Operator

## Environment Requirements

- **Python**: 3.9+ (Python 3.11 recommended)
- **Git**: 2.x+

## Installation

```bash
# Clone repository
git clone https://github.com/Genova-Nexus/Genova-Operator.git
cd Genova-Operator

# Initialize virtual environment
python -m venv _env
_env\Scripts\activate

# Install in editable mode
pip install -e .[dev]
```

## Running Tests

```bash
pytest
```
