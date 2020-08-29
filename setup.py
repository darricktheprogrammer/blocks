import setuptools

import blocks

with open("README.md", "r") as readme:
	long_description = readme.read()

setuptools.setup(
	name="Blocks",
	version=blocks.__version__,
	url="https://github.com/darricktheprogrammer/blocks",

	author="Darrick Herwehe",
	author_email="darrick@exitcodeone.com",

	description="A dead simple Plugin Manager",
	long_description=long_description,
	license='MIT',

	packages=setuptools.find_packages(),

	install_requires=[
		"attr"
		],

	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		"Operating System :: OS Independent",
		"Programming Language :: Python :: 3 :: Only",
		'Programming Language :: Python :: 3.6',
		"Topic :: Software Development :: Libraries",
	],
)
