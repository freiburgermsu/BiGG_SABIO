Acquire SABIO-RK Kinetics Data for an arbitrary BiGG model
___________________________________________________________________________________________

|License|

.. |PyPI version| image:: https://img.shields.io/pypi/v/bigg_sabio.svg?logo=PyPI&logoColor=brightgreen
   :target: https://pypi.org/project/bigg_sabio/
   :alt: PyPI version

.. |Actions Status| image:: https://github.com/freiburgermsu/bigg_sabio/workflows/Test%20bigg_sabio/badge.svg
   :target: https://github.com/freiburgermsu/bigg_sabio/actions
   :alt: Actions Status

.. |License| image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License

.. |Downloads| image:: https://pepy.tech/badge/bigg_sabio
   :target: https://pepy.tech/project/bigg_sabio
   :alt: Downloads


Reaction kinetics data is a pillar of biochemical research, and particularly computational biology. Sources of this data, however, are infrequently accessible to programmatic workflows, such as Dynamic Flux Balance Analysis (dFBA), which hinders research progress. The ``BiGG_SABIO`` library attempts to bridge this gab by scraping `SABIO-RK <http://sabio.h-its.org/>`_ kinetics data from any BiGG model-formatted JSON file, which is a powerful ability metabolic and dFBA researchers. Examples Notebook are available in the examples directory of the `BiGG_SABIO GitHub repository <https://github.com/freiburgermsu/BiGG_SABIO/examples>`_. Please submit errors, inquiries, or suggestions as `GitHub issues <https://github.com/freiburgermsu/BiGG_SABIO/issues>`_ where they can be addressed.


____________


----------------------
Installation
----------------------

``BiGG_SABIO`` is installed in a command prompt, Powershell, Terminal, or Anaconda Command Prompt via ``pip``::

 pip install bigg_sabio

-----------
__init__
-----------

The scraping is conducted through the ``SABIO_scraping`` object, which has four arguments:

.. code-block:: python

 import bigg_sabio
 bgsb = bigg_sabio.SABIO_scraping(bigg_model_path, bigg_model_name = None, export_model_content = False, verbose = False)

- *bigg_model_path* ``str``: specifies the path to the JSON file of the BiGG model that will be parsed.
- *bigg_model_name* ``str``: specifies the name of the BiGG model, which will be used to identify the model and name the output folder directory, where ``None`` defaults the name of the file from the ``bigg_model_path`` parameter.
- *export_model_content* ``str``: specifies where parsed information about the BiGG model will be  of the SBML file for the `BiGG model <http://bigg.ucsd.edu/>`_ that will be simulated. 
- *verbose* ``bool``: specifies whether simulation details and calculated values will be printed. This is valuable for trobuleshooting.


____________


Accessible content
______________________

A multitude of values are stored within the ``SABIO_scraping`` object that can be subsequently referenced and used in a workflow. The complete list of content within the ``SABIO_scraping`` object can be printed through the built-in ``dir()`` function:

.. code-block:: python

 # Scrape data for a BiGG model
 from bigg_sabio import SABIO_scraping
 bgsb = SABIO_scraping(bigg_model_path, bigg_model_name = None, export_model_content = False, verbose = False) 
 print(dir(bgsb))

The following list highlights stored content in the ``SABIO_scraping`` object after a simulation:

- *model* & *model_contents* ``dict``: The loaded BiGG model and a parsed form of the model, respectively, that are interpreted and guide the scraping of reaction enzymes.
- *sabio_df* ``Pandas.DataFrame``: A concatenated DataFrame that embodies all of the downloaded XLS files from the model enzymes.
- *paths*, *parameters*, & *variables* ``dict``: Dictionaries of 1) the essential paths from the scraping, which may be useful to locate and programmatically access each file; 2) important parameters that were parameterized; and 3) the variable values or files that derived from the scraping, respectively.
- *bigg_to_sabio_metabolites*, *sabio_to_bigg_metabolites*, & *bigg_reactions* ``dict``: Comprehensive dictionaries for the ID codes of BiGG metabolites and reactions, respectively. The ``bigg_to_sabio_metabolites`` dictionary is indexed with keys of BiGG ID and values of metabolite names that are recognized by SABIO and BiGG, whereas the ``bigg_to_sabio_metabolites`` dictionary is indexed with keys of SABIO metabolite names and values of the corresponding BiGG IDs.
- *driver* & *fp* ``Selenium.Webdriver``: The Firefox browser driver and profile, respectively, that are used programmatically by `Selenium functions <https://selenium-python.readthedocs.io/api.html>`_ to access and navigate the SABIO-RK database website.
- *step_number* ``int``: An indication of the progression within the scraping workflow, which is enumerated in the ``main()`` function of the script.