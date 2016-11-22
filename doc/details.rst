Saving Test Details
===================

Slash supports saving additional data about test runs, by attaching this data to the global result object.

Test Details
------------

Test details can be thought of as an arbitrary dictionary of values, keeping important information about the session that can be later browsed by reporting tools or plugins.

To set a detail, just use ``result.details.set``, accessible through Slash's global context:

.. code-block:: python

       def test_steering_wheel(car):
	   mileage = car.get_mileage()
	   slash.context.result.details.set('mileage', mileage)


Test Facts
----------

Facts are very similar to details but they are intended for a more strict set of values, serving as a basis for coverage matrices.

For instance, a test reporting tool might want to aggregate many test results and see which ones succeeded on model A of the product, and which on model B.

To set facts, use ``result.facts`` just like the details feature:

.. code-block:: python

       def test_steering_wheel(car):
	   slash.context.result.facts.set('is_van', car.is_van())


.. note:: facts also trigger the `fact_set <hooks.html#fact_set>`_ hook when set

.. note:: The distinction of when to use details and when to use facts is up for the user and/or the plugins that consume that information
