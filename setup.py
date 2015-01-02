import distutils.core

# Uploading to PyPI
# =================
# $ python setup.py register -r pypi
# $ python setup.py sdist upload -r pypi

version = '0.0'
distutils.core.setup(
        name='finalexam',
        version=version,
        author='Kale Kundert',
        url='https://github.com/kalekundert/finalexam',
        download_url='https://github.com/kalekundert/finalexam/tarball/'+version,
        license='LICENSE.txt',
        description="A simple unit testing framework.",
        long_description=open('README.rst').read(),
        keywords=['unit', 'testing', 'pythonic', 'library'],
        py_modules=['finalexam'],
        requires=['nonstdlib'],
)
