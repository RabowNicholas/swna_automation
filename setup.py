from setuptools import setup, find_packages

setup(
    name="swna-automation",
    version="1.0.0",
    description="SWNA Document Processing Automation - Processes DOL AR Acknowledgment letters automatically",
    author="SWNA",
    packages=find_packages(),
    install_requires=[
        "watchdog>=3.0.0",
        "pyairtable>=3.1.1", 
        "python-dotenv>=1.1.1",
        "pytesseract>=0.3.10",
        "Pillow>=10.0.0",
        "pdf2image>=1.16.3",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "swna-automation=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Legal",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)