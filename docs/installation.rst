Installation
============

Using uv (recommended)
----------------------

1. Install uv if you do not have it.
2. Sync project dependencies.

.. code-block:: bash

   uv sync

Install documentation dependencies

.. code-block:: bash

   uv pip install -r docs/requirements.txt

Build docs locally
------------------

.. code-block:: bash

   sphinx-build -b html docs docs/_build/html

Open generated documentation
----------------------------

Open ``docs/_build/html/index.html`` in your browser.
