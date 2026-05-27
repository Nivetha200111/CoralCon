from setuptools import setup, find_packages

setup(
    name="coralcon",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.40.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "fastapi>=0.115.0",
        "uvicorn>=0.32.0",
        "jinja2>=3.1.4",
        "python-dotenv>=1.0.1",
        "pydantic>=2.9.0",
        "httpx>=0.28.0",
        "notion-client>=2.0.0",
        "pytest>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "coralcon=coralcon.cli:cli",
        ],
    },
    python_requires=">=3.11",
)
