from setuptools import find_packages, setup

setup(
    name="yocli-tools",
    version="0.1.3",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyyaml",
    ],
    entry_points={
        'console_scripts': [
            'yocli=yocli.main:main',  # Defines the yocli command line tool
        ],
    },
    author="Yo",
    author_email="yoannes@gmail.com",
    description="A CLI tool to manage SSH connections and VSCode projects",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yoannes/yocli",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
