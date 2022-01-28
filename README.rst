Acquire SABIO-RK Kinetics Data for the Enyzmes of an arbitrary BiGG model
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


Reaction kinetics data is a pillar of biochemical research, and particularly computational biology. Sources of this data, however, are infrequently accessible to programmatic workflows, such as Dynamic Flux Balance Analysis (dFBA), which hinders research progress. The ``BiGG_SABIO`` library attempts to bridge this gab by scraping SABIO-RK kinetics data from any BiGG model-formatted JSON file, which is a powerful ability metabolic and dFBA researchers. Examples Notebook are available in the examples directory of the `BiGG_SABIO GitHub repository <https://github.com/freiburgermsu/BiGG_SABIO/examples>`_. Please submit errors, inquiries, or suggestions as `GitHub issues <https://github.com/freiburgermsu/BiGG_SABIO/issues>`_ where they can be addressed.



____________


----------------------
Installation
----------------------

``BiGG_SABIO`` is installed in a command prompt, Powershell, Terminal, or Anaconda Command Prompt via ``pip``::

 pip install bigg_sabio

-----------
__init__
-----------

The simulation environment is defined:

.. code-block:: python

 import bigg_sabio
 bgsb = bigg_sabio.SABIO_scraping(export_model_content = False, verbose = False)

- *bigg_model_path* ``str``: specifies path of the SBML file for the `BiGG model <http://bigg.ucsd.edu/>`_ that will be simulated. 
- *kinetics_data* ``dict``: specifies kinetics data that will be implemented into the COBRA model. The dictionary must follow the structure of ``<enzymes>`` -> ``<sources>`` -> ``Parameters`` & ``SubstitutedRateLaw``, where the last two keys must be precisely identical to those presented. The ``Parameters`` key must contains sub-dictionaries for each parameter that comprises the rate law expression for the reaction, which contain keys of ``unit``, ``chemical``, and ``value``:

 .. code-block:: json

  {
    "Acetate kinase": {
        "source_1": {
            "Parameters": {
                "A": {
                    "unit": "mM",
                    "chemical": "ADP C10H12N5O10P2",
                    "value": "1.0"
                    },
                "B":{
                    "unit": "mM",
                    "chemical": "Acetyl phosphate",
                    "value": "0.8"
                    }
            },
            "SubstitutedRateLaw": "(68.0/milli*A*B)/(50.0*micro*0.34*micro+360.0*micro*B+0.34*micro*A+A*B)"
         }
     }
  }
       
The ``SubstitutedRateLaw`` key must contain a mathematically valid string of the reaction rate law that can be evaluated through the `eval() built-in function <https://pythongeeks.org/python-eval-function/>`_ of Python. Each of the variables in the ``SubstitutedRateLaw`` expression must be defined in the ``Parameters`` key. The ``milli`, ``micro``, and ``nano`` words can be inserted into the reaction string to convert molar units into the base molar units. The kinetics_data content can be expanded with additional keys within each source to provide provenance or metadata, at the user's discretion, as long as the aforementioned core information remains in the data dictionary:
            
.. code-block:: json

  {
    "Acetate kinase": {
        "source_1": {
            "Organism": "Escherichia coli",
            "Parameters": {
                "A": {
                    "unit": "mM",
                    "chemical": "ADP C10H12N5O10P2",
                    "v": "1.0"
                    },
                "B":{
                    "unit": "mM",
                    "chemical": "Acetyl phosphate",
                    "value": "0.8"
                    }
            },
            "PubMedID": "4362687.0"
            "Publication": "Janson CA, Cleland WW: The inhibition of acetate, pyruvate, and 3-phosphogylcerate kinases by chromium adenosine triphosphate, J Biol Chem 1974 (249) , 2567-71",
            "SubstitutedRateLaw": "(68.0/milli*A*B)/(50.0*micro*0.34*micro+360.0*micro*B+0.34*micro*A+A*B)",
            "Temperature": "25.0",
            "pH": "7.0",
            "SabioReactionID": 71,
        }
    }
 }
 
- *verbose* ``bool``: specifies whether simulation details and calculated values will be printed. This is valuable for trobuleshooting.
- *printing* ``bool``: specifies whether simulation results will be printed. 
- *jupyter* ``bool``: specifies whether simulation is being conducted in a Jupyter notebook, in which case the printed DataFrames will be expressed with the ``display()`` function. 

            
----------------------
simulate()
----------------------

The BiGG model is simulated with the parameterized kinetics data over the defined time and conditions:

.. code-block:: python

 dfba.simulate(self, total_time, timestep, initial_concentrations = None, temperature = 25, p_h = 7, visualize = True)


- *total_time* ``float``: specifies total quantity of minutes for which the simulation will be conducted.
- *timestep* ``float``: specifies the timestep in minutes of the simulation.
- *initial_concentrations* ``dict``: specifies initial concentrations of the simulated metabolites, which must be identified precisely with the BiGG names for the chemicals. This can be conveniently achieved through the ``dfba.bigg_metabolite_name()`` function of the ``dFBA`` object, which accepts a metabolite BiGG ID string and returns the corresponding metabolite BiGG name. The `BiGG_metabolites, parsed.json` file that is provided with ``bigg_sabio``, which is a parsed version of the `BiGG metaoblites chart <http://bigg.ucsd.edu/static/namespace/bigg_models_metabolites.txt>`, can also be manually searched to identify the appropriate format of the chemical name. Any chemicals that are not defined by initial_concentrations will be assigned an initial concentration of 0, which effectively renders the simulation results for these chemicals to be a relative change instead of an absolute change in concentration.
- *temperature* & *p_h* ``float``: optionally specify the temperature and pH at which the simulation will occur, respective, which allows the user to select the closest matched data in a large kinetics data set for the simulation.
- *visualize* ``bool``: specifies whether the simulation results will be visually depicted.


----------------------
export()
----------------------

The simulation results and parameters can be exported to the specified folder:

.. code-block:: python

 dfba.export(export_directory = None, export_name = None)

- *export_directory* ``str``: optionally specifies a path to where the content will be exported, where `None` selects the current working directory.
- *export_name* ``str``: optionally specifies a name for the folder of exported content, where `None` enables the code to design a unique folder name for the information.



____________


Accessible content
______________________

A multitude of values are stored within the ``dFBA`` object, and can be subsequently used in a workflow. The complete list of content within the ``dFBA`` object can be printed through the built-in ``dir()`` function in the following example sequence:

.. code-block:: python

 # conduct a ROSSpy simulation
 from bigg_sabio import SABIO_scraping
 bgsb = SABIO_scraping(bigg_model_path, reaction_kinetics)
 bgsb.simulate(total_time, timestep)
 bgsb.export()
 
 # evaluate the ROSSpy simulation contents
 print(dir(dfba))

The following list highlights stored content in the ``dFBA`` object after a simulation:

- *model* ``COBRA model``: A `cobra.core.model <https://cobrapy.readthedocs.io/en/latest/autoapi/cobra/core/model/index.html>`_ object that defines the GEM model of the FBA simulation.
- *concentrations* & *fluxes* ``DataFrame``: `Pandas DataFrames <https://pandas.pydata.org/pandas-docs/stable/reference/frame.html>`_ that contain the ``mM`` concentrations for each metabolite and ``mmol/g_(dw)/hr`` fluxes for each reaction, respectively.
- *kinetics_data* ``dict``: A dictionary of the kinetics data that will constrain the Cobra GEM model.
- *timestep_value* ``float``: The value of the parameterized timestep.
- *bigg_metabolites* ``dict``: A dictionary of the BiGG ids with their names as values, which is the premise of the ``bigg_metabolite_name()`` parsing function in the ``dFBA`` object. This may be exported and analyzed to parse the ID <-> name interconversion of BiGG metabolites beyond the ``bigg_metabolite_name()`` function.
- *cell_dry_mass* & *cell_liters* ``float``: The `dry mass <https://doi.org/10.1101/2021.12.30.474524>`_ and `volume <https://doi.org/10.1128/AEM.00117-14>`_ of a single cell, in base units of grams and liters, respectively. The citations for these values are hyperlinked with the respective value.
- *changed* & *unchanged* ``set``: The unique and exclusive sets of metabolites that changed or did not change in concentration over the simulation, respectively.
- *constrained* ``list``: The list of reactions that were constrained in the Cobra model with the calculated flux from the kinetics data.
- *solutions* ``list``: A list of the Cobra solutions from the simulation -- one per timestep -- that are constitute the columns of the fluxes DataFrame.