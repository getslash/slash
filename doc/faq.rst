FAQ
---

What is the Difference Between Slash and Pytest/Nose/Unittest?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We would first like to point out that both *Nose* and Python's built-in ``unittest`` were built for building and running unit tests. Unittest provides a decent runner, whereas *Nose* is more of an evolved runner that supports plugins. Both try not to get involved too much in your project's test code, and assume you are running unittest-based tests, or not far from it.

*Pytest*, on the other hand, took the next step - it's not only a great test runner, but provides more utilities and infrastructure for your tests, like fixtures, parametrization etc. We personally love pytest, and use it to test Slash itself, as you can see from our code.

However, the main difference is in the project's focus. Pytest was created as a successor to nose/unittest, and as such its primary focus tends to remain around unit tests. This implies certain defaults (like stdout/stderr capturing) and certain sets of features which are more likely to be implemented for it.

The main project for which we wrote Slash involved testing an external product. As such, it was less about maintaining individual state for each test and setting it up again later, and more about building a consistent state for the entire test session -- syncing with the test "subject" before the first test, performing validations between tests, recycling objects and entities between tests etc. What was missing for us in Pytest became clear after a certain period of active development -- Pytest, being focused around the tests being written, lacks (some) facilities to deal with everything around and between the tests.

One specific example for us was widely-scoped cleanups (like tests registering cleanups that are to happen at the end of the session or module) - in this case it was difficult to tie the error to the entity that created the cleanup logic. There are more examples of how Slash focuses on the testing session itself and its extensibility - the concept of session errors is much better defined in Slash, it includes mechanisms for controlling plugin dependencies, multiple levels of customizations and a hierarchical configuration mechanism. There are also features that Slash provides that Pytest does not, like better logging control, advanced fixture parametrization, early-catch exception handling and more - with even more yet to be shipped.

Another difference is that while pytest can be loosely thought of as a tool, Slash can be thought of as a framework. It puts much more emphasis on letting you build on top of it, set up your environment and integrate with external services (we ourselves built Backslash as a centralized reporting solution for it, for instance). Slash eventually aims at helping you evolve your own testing solution with it.

In the end, the distinction isn't clear-cut though, and different people might find different tools better suited for them. This is great - having choice when it comes to which tool to use is a good thing, and we embrace this fact.
