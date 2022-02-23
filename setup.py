# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.rst') as file:
    readme = file.read()

setup(
  name = 'BiGG_SABIO',      
  package_dir = {'scraper':'bigg_sabio'},
  packages = find_packages(),
  package_data = {
	'bigg_sabio':['l2pnahxq.scraper/*', 'BiGG_metabolite_names, parsed.json', 
    'BiGG_metabolites, parsed.json', 'BiGG_reactions, parsed.json', 'geckodriver.exe']
  },
  version = '0.0.1',
  license = 'MIT',
  description = "Scrapes SABIO-RK for enzyme kinetics data for given BiGG Model for dFBA simulation.", 
  long_description = readme,
  author = 'Andrew Freiburger, Ethan Chan',               
  author_email = 'andrewfreiburger@gmail.com',
  url = 'https://github.com/freiburgermsu/BiGG_SABIO',   
  keywords = ['dFBA', 'FBA', 'BiGG', 'biochemistry', 'scraping', 'metabolism', 'SABIO', 'SABIO-RK', 'kinetics', "bioinformatics"],
  install_requires = ['selenium', 'scipy', 'pandas', 'numpy']
)