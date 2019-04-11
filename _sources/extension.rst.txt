How to Extend
=============
**mecoSHARK** can be extended by adding new processors for other programming languages.

All processors are stored in the mecoshark/processor folder. There are conditions, which must be fulfilled by the
backends so that it is accepted by the **mecoSHARK**:

1. The \*.py file for this backend must be stored in the mecoshark/processor folder.
2. It must inherit from :class:`~mecoshark.processor.baseprocessor.BaseProcessor.threshold` and implement the methods defined there.

The process of chosing the backend is the following:

*	Via sloccount the number of files get calculated that have the same programming languages

*   In each processor a threshold is defined :func:`~` that shows when the processor will gets executed (e.g., 0.5 means that at least 50% of all files must have this programming language

*   Afterwards the processor calls :func:`~mecoshark.processor.baseprocessor.BaseProcessor.process`

There are several important things to note:

1.	If you want to use a logger for your implementation, get it via

	.. code-block:: python

		logger = logging.getLogger("processor")


2.	The execution logic is in the application class and explained here :class:`~mecoshark.mecosharkapp.MecoSHARK`.

3. If you want to have an example how to implement this class, look at
:class:`~mecoshark.processor.pythonprocessor.PythonProcessor`

