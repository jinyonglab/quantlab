from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="investlab",
    version="0.1.0",
    author="InvestLab Team",
    author_email="your-email@example.com",
    description="A quantitative investment research platform for A-share market",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/InvestLab",
    packages=find_packages(exclude=["tests", "tests.*", "venv", "venv.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "investlab=main:main",
            "investlab-web=web_server:main",
        ],
    },
    keywords="quantitative trading, backtest, investment, a-share, python, finance",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/InvestLab/issues",
        "Source": "https://github.com/yourusername/InvestLab",
        "Documentation": "https://github.com/yourusername/InvestLab/wiki",
    },
)
