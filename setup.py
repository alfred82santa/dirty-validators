import os
import ast
from setuptools import setup


path = os.path.join(os.path.dirname(__file__), 'dirty_validators', '__init__.py')

with open(path, 'r') as file:
    t = compile(file.read(), path, 'exec', ast.PyCF_ONLY_AST)
    for node in (n for n in t.body if isinstance(n, ast.Assign)):
        if len(node.targets) != 1:
            continue

        name = node.targets[0]
        if not isinstance(name, ast.Name) or \
                name.id not in ('__version__', '__version_info__', 'VERSION'):
            continue

        v = node.value
        if isinstance(v, ast.Str):
            version = v.s
            break
        if isinstance(v, ast.Tuple):
            r = []
            for e in v.elts:
                if isinstance(e, ast.Str):
                    r.append(e.s)
                elif isinstance(e, ast.Num):
                    r.append(str(e.n))
            version = '.'.join(r)
            break

setup(
    name='dirty-validators',
    url='https://github.com/alfred82santa/dirty-validators',
    author='alfred82santa',
    version=version,
    author_email='alfred82santa@gmail.com',
    packages=['dirty_validators'],
    include_package_data=True,
    test_suite="nose.collector",
    description="Validate library for python 3",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    tests_require="nose",
    zip_safe=True,
)
