========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor|
        |
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/checkon/badge/?style=flat
    :target: https://readthedocs.org/projects/checkon
    :alt: Documentation Status


.. |travis| image:: https://travis-ci.org/python-checkon/checkon.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/python-checkon/checkon

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/python-checkon/checkon?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/python-checkon/checkon

.. |version| image:: https://img.shields.io/pypi/v/checkon.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/pypi/checkon

.. |commits-since| image:: https://img.shields.io/github/commits-since/python-checkon/checkon/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/python-checkon/checkon/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/checkon.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/pypi/checkon

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/checkon.svg
    :alt: Supported versions
    :target: https://pypi.org/pypi/checkon

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/checkon.svg
    :alt: Supported implementations
    :target: https://pypi.org/pypi/checkon


.. end-badges

An example package. Generated with cookiecutter-pylibrary.

* Free software: BSD 2-Clause License

Installation
============

::

    pip install checkon

Documentation
=============


https://checkon.readthedocs.io/


Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
