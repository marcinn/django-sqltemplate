import os
from setuptools import setup, find_packages


with open(
    os.path.join(os.path.dirname(__file__), 'README.md'),
    encoding='utf-8'
) as fh:
    long_description = fh.read()


setup(name='django-sqltemplate',
      version='0.5.2.post2',
      description='Database querying tool for Django, based on SQL templates',
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
        ],
      author='Marcin Nowak',
      author_email='marcin.j.nowak@gmail.com',
      url='https://github.com/marcinn/django-sqltemplate',
      install_requires=['sqltemplate>=0.5.0,<0.6.0'],
      keywords='web python django sql template',
      packages=find_packages('.'),
      include_package_data=True,
      long_description=long_description,
      long_description_content_type='text/markdown',
      test_suite='nose.collector',
      zip_safe=True,
      )
