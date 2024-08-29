import os
import sys
import shutil
import argparse
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

def compile_project(input_dir, output_dir, remove_originals=False):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get all Python files in the input directory
    py_files = [f for f in os.listdir(input_dir) if f.endswith('.py')]

    # Prepare extension modules
    extensions = []
    for py_file in py_files:
        module_name = os.path.splitext(py_file)[0]
        source_path = os.path.join(input_dir, py_file)
        extensions.append(Extension(module_name, [source_path]))

    # Set up a custom build_ext command to specify output directory
    class custom_build_ext(build_ext):
        def get_ext_fullpath(self, ext_name):
            filename = self.get_ext_filename(ext_name)
            return os.path.join(output_dir, filename)

    # Compile the extensions
    setup(
        ext_modules=cythonize(
            extensions,
            compiler_directives={'language_level': "3"},
        ),
        cmdclass={'build_ext': custom_build_ext},
        script_args=['build_ext']
    )

    # Clean up temporary directories and files
    dirs_to_remove = ['build', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

    files_to_remove = [f for f in os.listdir(input_dir) if f.endswith('.c')]
    for file_name in files_to_remove:
        os.remove(os.path.join(input_dir, file_name))

    # Optionally remove original Python files
    if remove_originals:
        for py_file in py_files:
            os.remove(os.path.join(input_dir, py_file))

    print(f"Compilation complete. Compiled files are in: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile Python project using Cython")
    parser.add_argument("input_dir", help="Input directory containing Python files")
    parser.add_argument("output_dir", help="Output directory for compiled files")
    parser.add_argument("--remove-originals", action="store_true", help="Remove original Python files")

    args = parser.parse_args()

    compile_project(args.input_dir, args.output_dir, args.remove_originals)