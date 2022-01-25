# BiGG_SABIO
A module to acquire reaction kinetics data from SABIO-RK for any BiGG model


### scraping
The scraping section scrapes the SABIO kinetic database for the reactions that are defined in a GEM model, which is consistent with [the declaration of the database for access to their data](https://web.archive.org/web/20211019181435/http://sabio.h-its.org/layouts/content/webservices.gsp). These scraping efforts are organized into a JSON file, which can parameterized in dFBA simulations.
