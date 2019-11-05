import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="moln",
    version="0.0.1",
    author="Johan Stenberg",
    author_email="johan.stenberg@microsoft.com",
    description="Stupid, simple Azure client library built for the rest of us",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/johanste/moln",
    packages= ['moln'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "azure-storage-blob<13.0.0,>=12.0.0",
        "azure-identity<2.0.0,>=1.0.0"
    ],
    python_requires='>=3.6',
)