# Contributing to FluxCRUD

Thank you for your interest in contributing to FluxCRUD! We welcome contributions from the community to help make this project better.

## 🛠️ Development Setup

FluxCRUD uses [uv](https://github.com/astral-sh/uv) for dependency management and project setup.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/mahimailabs/fluxcrud.git
    cd fluxcrud
    ```

2.  **Install dependencies**:
    ```bash
    uv sync --all-extras --dev
    ```

3.  **Activate the virtual environment**:
    ```bash
    source .venv/bin/activate
    ```

## Running Tests

We use `pytest` for testing. Ensure all tests pass before submitting a PR.

```bash
uv run pytest
```

## Code Quality

We use `ruff` for linting and formatting.

```bash
uv run ruff check .
uv run ruff format .
```

## Type Checking

We use `mypy` for type checking.

```bash
uv run mypy fluxcrud
```

## 📝 Submission Guidelines

1.  Fork the repository.
2.  Create a new branch for your feature or fix (`git checkout -b feature/amazing-feature`).
3.  Commit your changes with clear messages.
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## 🤝 Community

If you have questions or want to discuss ideas, please open an issue or start a discussion on GitHub.
