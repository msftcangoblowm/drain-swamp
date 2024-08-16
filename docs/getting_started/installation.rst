Installation
=============

``drain-swamp`` is available at PyPi :pypi_org:`drain-swamp`,
and can be installed from ``pip`` or source as follows.

.. card::

    .. tabs::

        .. code-tab:: bash From ``pip``

            python -m pip install --upgrade drain-swamp

        .. code-tab:: bash From source

            git clone https://github.com/msftcangoblowm/drain-swamp
            cd drain-swamp
            python -m venv .venv
            . .venv/bin/activate
            python -m pip install --upgrade -r requirements/kit.lock -r requirements/prod.lock
            python -m build -C--set-lock="1" -C--kind="tag"
            python -m pip install --upgrade dist/drain_swamp-$(python src/drain_swamp/cli_igor.py tag)-py3-none-any.whl


.. raw:: html

    <div class="white-space-20px"></div>
