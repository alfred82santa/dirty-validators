from setuptools import setup

setup(
    name='dirty-validators',
    url='https://github.com/alfred82santa/dirty-validators',
    author='alfred82santa',
    version='0.1.1',
    author_email='alfred82santa@gmail.com',
    packages=['dirty_validators'],
    include_package_data=True,
    test_suite="nose.collector",
    tests_require="nose",
    zip_safe=True,
)
