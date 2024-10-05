The mission
============

``drain-swamp`` mission is intended to be a Python build backend for packages
that have generated files. Build plugins generate the files during the
build process.

The ultimate goal has always been to go crazy with microservices.

A jargon term for,

.. code-block:: text

   Front end blocks when calling heavy background processes, waiting
   for those background processes to complete.

To avoid a blocked front end, send heavy background work to a message queue, such as
RabbitMQ or Kafta.

The communication packets should have a schema preventing spam nonsense packets being
tossed at either the workers or consumers (the front end app).

The schema is used to create a file used by both front end and workers. Those
generated files are included in the package.

If those components become out of date, non-technical users that download
the source code most likely won't be able to get the app to work.

To prevent the possibility, the build process should recreate those files.

It not the role of the end user to generate those files. How and why
should possibly expect them to know how to do that?
