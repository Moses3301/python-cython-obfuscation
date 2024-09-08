![Dragon Guarding Treasure](images/dragon.png)

# Python Cython Obfuscation

This project provides a template for compiling Python code with Cython to improve performance and make the code harder to reverse-engineer.

## Features

- **Compile Python Code**: Convert Python files to compiled C extensions (`.pyd` or `.so` files) using Cython.
- **Obfuscation**: Makes the Python code more difficult to reverse-engineer.
- **Flexible File Handling**:
  - Option to keep or remove the original `.py` files after compilation.
  - Specify a custom output directory for compiled files.

## Prerequisites

- Python 3.x
- Cython
- A C compiler (e.g., GCC on Linux/macOS, MSVC on Windows)

## Setup and Compilation

### 1. Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/Moses3301/python-cython-obfuscation.git
cd python-cython-obfuscation
```

### 2. Install Cython

Install Cython if you haven't already

```bash
pip install cython
```

### 3.Compile the Python Code

```bash
python setup.py input_directory output_directory [--remove-originals]
```


## Fixes and Improvements 
- [ ] Resolved issues with module names that begin with non-letter characters
- [ ] Integrated obfuscation as a core part of the process.
- [ ] Enhanced the obfuscation script to support multi-file projects, enabling better handling of larger codebases.

