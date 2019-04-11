============
Introduction
============

.. _sourcemeter: https://www.sourcemeter.com/download/

This introduction will show how to use **mecoSHARK**. Furthermore, we list all requirements for this tool here, so that an
easy installation is possible.

**mecoSHARK** collects over 70 different static product metrics and over 15 different code clone metrics.
A full list of the calculated metrics can be found in our database documentation.
Furthermore, mecoFoo detects type-2 clones in the code.


The tool works on a revision of a repository, where `vcsSHARK <https://github.com/smartshark/vcsSHARK>`_ was executed
beforehand. Generally, mecoSHARK works in two phases: first, the programming language of the project is automatically
detected by using sloccount. If a given threshold is reached (\% of files that are written in a
certain programming language), we execute the metrics calculator and clone parser for this kind of programming language.
Currently, we support Java and Python.
Second, the results are parsed and stored in the MongoDB using the mongoengine ORM library.

For the metrics calculation and clone detection we use sourcemeter_.
Additionally, SourceMeter provides the option to build the project via Ant or Maven and calculate the metrics afterwards.
We have implemented, but currently disabled, this feature in **mecoSHARK**, as it is not tested in-depth.

We use a vanilla Ubuntu 16.04 operating system as basis for the steps that we describe. If necessary, we give hints
on how to perform this step with a different operating system.


.. WARNING:: This software is still in development.



Model Documentation
===================
The documentation for the used database models can be found here: https://smartshark.github.io/pycoSHARK/api.html


.. _installation:

Installation
============
The installation process needs a little bit more effort, as sourcemeter_ can not be publicly distributed. For a vanilla
Ubuntu 16.04, we need to install the following packages:

.. code-block:: bash

	$ sudo apt-get install git python3-pip python3-cffi


You also need to install JAVA. For more information follow this link: https://wiki.ubuntuusers.de/Java/Installation

After these requirements are met, first clone the
**mecoSHARK** `repository <https://github.com/smartshark/mecoSHARK/>`_ repository to a folder you want. In the
following, we assume that you have cloned the repository to **~/mecoSHARK**. Afterwards,
the installation of **mecoSHARK** can be done in two different ways:

via Pip
-------
.. code-block:: bash

	$ sudo pip3 install https://github.com/smartshark/mecoSHARK/zipball/master --process-dependency-links

via setup.py
------------
.. code-block:: bash

	$ sudo python3.5 ~/mecoSHARK/setup.py install

.. NOTE::
	It is advisable to change the location, where the logs are written to.
	They can be changed in the **~/mecoSHARK/mecoshark/loggerConfiguration.json**. There are different file handlers defined.
	Just change the "filename"-attribute to a location of your wish.


Afterwards, you need to download sourcemeter_ and create the following structure:

Overall structure:

.. image:: images/folder_structure.png

Sloccount structure:

.. image:: images/sloccount.png

.. WARNING:: Make sure, that your $JAVA_HOME is set correctly!

.. WARNING:: Make sure, that /external/sloccount2.26 is in your $PATH.


Furthermore, you need a running MongoDB. The process of setting up a MongoDB is explained here:
https://docs.mongodb.com/manual/installation/


Tests
=====
The tests of **mecoSHARK** can be executed by calling

	.. code-block:: bash

		$ python3.5 ~/mecoSHARK/setup.py test

The tests can be found in the folder "tests".

.. WARNING:: The generated tests are not fully complete. They just test the basic functionality.


Execution
==========
In this chapter, we explain how you can execute **mecoSHARK**. Furthermore, the different execution parameters are
explained in detail.

1) Choose a project from which you want to collect metrics

2) Clone this project

3) Make sure that your MongoDB is running!

	.. code-block:: bash

		$ sudo systemctl status mongodb

4) Execute `vcsSHARK <https://github.com/smartshark/vcsSHARK>`_ on this project

5) Set the project you want to analyze to a specific revision

6) Execute **mecoSHARK** by calling

	.. code-block:: bash

		$ python3.5 ~/mecoSHARK/main.py


**mecoSHARK** supports different commandline arguments:

.. option:: --help, -h

	shows the help page for this command

.. option:: --version, -v

	shows the version

.. option:: --db-user <USER>, -U <USER>

	Default: None

	mongodb user name

.. option:: --db-password <PASSWORD>, -P <PASSWORD>

	Default: None

	mongodb password

.. option:: --db-database <DATABASENAME>, -DB <DATABASENAME>

	Default: smartshark

	database name

.. option:: --db-hostname <HOSTNAME>, -H <HOSTNAME>

	Default: localhost

	hostname, where the mongodb runs on

.. option:: --db-port <PORT>, -p <PORT>

	Default: 27017

	port, where the mongodb runs on

.. option:: --db-authentication <DB_AUTHENTICATION> -a <DB_AUTHENTICATION>

	Default: None

	name of the authentication database

.. option:: --ssl

	enables ssl for the connection to the mongodb

.. option:: --debug <DEBUG_LEVEL>, -d <DEBUG_LEVEL>

	Default: DEBUG

	Debug level (INFO, DEBUG, WARNING, ERROR)

.. option:: --repository_url <URL>, -u <URL>

	Required

	URL of the project (e.g., https://github.com/smartshark/mecoSHARK)

.. option:: --revision <REVISION_HASH>, -r <REVISION_HASH>

	Required

	Hash of the revision that is analyzed

.. option:: --input <PATH>, -i <PATH>

	Required

	Path to the repository that should be analyzed

.. option:: --output <PATH>, -o <PATH>

	Required

	Path to a folder that can  be used as output

.. option:: --makefile-contents

	Default: None

	Contents of the makefile (only for c/c++/c#), e.g., "./configure\nmake".



Tutorial
========

In this section we show step-by-step how you can store metrics of the
`Zookeeper <https://github.com/apache/zookeeper>`_ project in the MongoDB

1.	First, you need to have a mongodb running (version 3.2+).
How this can be achieved is explained here: https://docs.mongodb.org/manual/.

.. WARNING::
	Make sure, that you activated the authentication of mongodb
	(**mecoSHARK** also works without authentication, but with authentication it is much safer!).
	Hints how this can be achieved are given `here <https://docs.mongodb.org/manual/core/authentication/>`_.

2. Add zookeeper to the projects table in MongoDB.

	.. code-block:: bash

		$ mongo
		$ use smartshark
		$ db.project.insert({"name": "Zookeeper"})

3. Install `vcsSHARK <https://github.com/smartshark/vcsSHARK>`_

4. Enter the **vcsSHARK** directory via

	.. code-block:: bash

		$ cd vcsSHARK

5. Clone the Zookeeper repository to your home directory (or another place)

	.. code-block:: bash

		$ git clone https://github.com/apache/zookeeper ~/Zookeeper

6. Execute **vcsSHARK**:

	.. code-block:: bash

		$ cd ~/vcsSHARK
		$ python3.5 ~/vcsSHARK/vcsshark.py -D mongo -DB smartshark -H localhost -p 27017 -n Zookeeper --path ~/Zookeeper

7. Set Zookeeper to the revision: edf75b5e31f0d9e2fbfadbd95bae9d1d6c4737f6

	.. code-block:: bash

		$ cd ~/Zookeeper
		$ git reset --hard edf75b5e31f0d9e2fbfadbd95bae9d1d6c4737f6

7. Install **mecoSHARK**. An explanation is given above.

8. Enter the **mecoSHARK** directory via

	.. code-block:: bash

		$ cd ~/mecoSHARK

9. Test if everything works as expected

	.. code-block:: bash

		$ python3.5 main.py --help

	.. NOTE:: If you receive an error here, it is most likely, that the installation process failed.

10. Create an empty directory

	.. code-block:: bash

		$ mkdir ~/temp

5. Execute **mecoSHARK**:

	.. code-block:: bash

		$ cd ~/mecoSHARK
		$ python3.5 main.py -i ~/Zookeeper -o ~/temp -r edf75b5e31f0d9e2fbfadbd95bae9d1d6c4737f6 -u https://github.com/apache/zookeeper


Thats it. The results are explained in the database documentation
of `SmartSHARK <http://smartshark2.informatik.uni-goettingen.de/documentation/>`_.