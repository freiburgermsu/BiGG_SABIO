# -*- coding: utf-8 -*-
"""
@authors: Ethan Sean Chan, Andrew Philip Freiburger
"""
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from selenium import webdriver

from scipy.constants import minute, hour, milli, nano, micro
from pprint import pprint
from shutil import rmtree
from glob import glob
import numpy as np
import datetime
import pandas
import json, time, re, os


def isnumber(string):
    try:
        string = str(string)
        string = string.strip()
        if re.sub('([0-9\.])', '',string) == '':
            return True
    except:
        return False
    
def average(num_1, num_2 = None):
    if isnumber(num_1): 
        if isnumber(num_2):
            numbers = [num_1, num_2]
            return sum(numbers) / len(numbers)
        else:
            return num_1
    elif type(num_1) is list:
        summation = total = 0
        for num in num_1:
            if num is not None:
                summation += num
                total += 1
        if total > 0:
            return summation/total
        raise None # ValueError('The arguments must be numbers or a list of numbers')
    elif isnumber(num_2):
        return num_2
    else:
        raise None # ValueError('The arguments must be numbers or a list of numbers')
    
    
    

# encoding the final JSON
class NumpyEncoder(json.JSONEncoder):     # sourced from https://github.com/hmallen/numpyencoder
    """ Custom encoder for numpy data types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):

            return int(obj)

        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)

        elif isinstance(obj, (np.complex_, np.complex64, np.complex128)):
            return {'real': obj.real, 'imag': obj.imag}

        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()

        elif isinstance(obj, (np.bool_)):
            return bool(obj)

        elif isinstance(obj, (np.void)): 
            return None

        return json.JSONEncoder.default(self, obj)
    
    
# allows case insensitive dictionary searches
class CaseInsensitiveDict(dict):   # sourced from https://stackoverflow.com/questions/2082152/case-insensitive-dictionary
    @classmethod
    def _k(cls, key):
        return key.lower() if isinstance(key, str) else key

    def __init__(self, *args, **kwargs):
        super(CaseInsensitiveDict, self).__init__(*args, **kwargs)
        self._convert_keys()
        
    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(self.__class__._k(key))
    
    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(self.__class__._k(key), value)
        
    def __delitem__(self, key):
        return super(CaseInsensitiveDict, self).__delitem__(self.__class__._k(key))
    
    def __contains__(self, key):
        return super(CaseInsensitiveDict, self).__contains__(self.__class__._k(key))
    
    def has_key(self, key):
        return super(CaseInsensitiveDict, self).has_key(self.__class__._k(key))
    
    def pop(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).pop(self.__class__._k(key), *args, **kwargs)
    
    def get(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).get(self.__class__._k(key), *args, **kwargs)
    
    def setdefault(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).setdefault(self.__class__._k(key), *args, **kwargs)
    
    def update(self, E=None, **F):
        super(CaseInsensitiveDict, self).update(self.__class__(E))
        super(CaseInsensitiveDict, self).update(self.__class__(**F))
        
    def _convert_keys(self):
        for k in list(self.keys()):
            v = super(CaseInsensitiveDict, self).pop(k)
            self.__setitem__(k, v)


class SABIO_scraping():
#     __slots__ = (str(x) for x in [progress_file_prefix, xls_download_prefix, is_scraped_prefix, scraped_entryids_prefix, sel_raw_data, processed_xls, entry_json, scraped_model, bigg_model_name_suffix, output_directory, progress_path, raw_data, is_scraped, scraped_entryids_path, xls_csv_file_path, entryids_json_file_path, scraped_model_path, bigg_model, step_number, cwd])
    
    def __init__(self,
                 bigg_model_path: str,        # the JSON version of the BiGG model
                 bigg_model_name: str = None,  # the name of the BiGG model
                 export_model_content: bool = False,
                 verbose: bool = False
                 ):
        self.export_model_content = export_model_content 
        self.verbose = verbose
        self.count = 0
        self.paths = {}
        
        self.parameters = {}
        self.parameters['general_delay'] = 2
        
        self.variables = {}
        
        # load BiGG dictionary content 
        self.paths['root_path'] = os.path.dirname(__file__)
        self.bigg_to_sabio_metabolites = json.load(open(os.path.join(self.paths['root_path'],'BiGG_metabolites, parsed.json')))
        self.sabio_to_bigg_metabolites = json.load(open(os.path.join(self.paths['root_path'],'BiGG_metabolite_names, parsed.json')))
        self.bigg_reactions = json.load(open(os.path.join(self.paths['root_path'],'BiGG_reactions, parsed.json')))
        
        # load the BiGG model content
        if os.path.exists(self.bigg_model_path):
            self.model = json.load(open(self.bigg_model_path))
        else:
            raise ValueError('The BiGG model file does not exist')
            
        self.bigg_model_name = bigg_model_name 
        if bigg_model_name is None:
            self.bigg_model_name = re.search("([\w+\.?\s?]+)(?=\.json)", self.bigg_model_path).group()
            

    #Clicks a HTML element with selenium by id
    def _click_element_id(self,n_id):
        element = self.driver.find_element_by_id(n_id)
        element.click()
        time.sleep(self.parameters['general_delay'])
        
    def _wait_for_id(self,n_id):
        while True:
            try:
                element = self.driver.find_element_by_id(n_id)   #!!! what is the purpose of this catch?
                break
            except:
                time.sleep(self.parameters['general_delay'])
        

    #Selects a choice from a HTML dropdown element with selenium by id
    def _select_dropdown_id(self,n_id, n_choice):
        element = Select(self.driver.find_element_by_id(n_id))
        element.select_by_visible_text(n_choice)
        time.sleep(self.parameters['general_delay'])
        
    """
    --------------------------------------------------------------------
        STEP 0: GET BIGG MODEL TO SCRAPE AND SETUP DIRECTORIES AND PROGRESS FILE
    --------------------------------------------------------------------    
    """

    def start(self):
        # define core paths
        self.paths['cwd'] = os.path.dirname(os.path.realpath(self.bigg_model_path))        # what is the point of the relative path within the directory name?
        self.paths['output_directory'] = os.path.join(self.paths['cwd'],f"scraping-{self.bigg_model_name}")       
        self.paths['scraped_model_path'] = os.path.join(self.paths['output_directory'], "scraped_model.json")
        
        if not os.path.isdir(self.paths['output_directory']):        
            os.mkdir(self.paths['output_directory'])
                    
        # monitor the scrapping progress
        self.paths['progress_path'] = os.path.join(self.paths['output_directory'], "current_progress.txt")
        self.step_number = 1
        self._progress_update(self.step_number)
        if os.path.exists(self.paths['progress_path']):
            with open(self.paths['progress_path'], "r") as f:
                self.step_number = int(f.read(1))
                if not re.search('[1-5]',str(self.step_number)):
                    raise ImportError("Progress file malformed. Create a < current_progress.txt > file with a < 1-5 > digit to signify the current scrapping progress.")

        # define the data directories
        self.paths['raw_data'] = os.path.join(self.paths['output_directory'], 'downloaded_xls') 
        if not os.path.isdir(self.paths['raw_data']):
            os.mkdir(self.paths['raw_data'])

        self.paths['processed_data'] = os.path.join(self.paths['output_directory'], 'processed_data') 
        if not os.path.isdir(self.paths['processed_data']):
            os.mkdir(self.paths['processed_data'])

        # define file paths and import content from an interupted scrapping        
        self.paths['is_scraped'] = os.path.join(self.paths['raw_data'], "is_scraped.json")
        self.variables['is_scraped'] = {}
        if os.path.exists(self.paths['is_scraped']):
            with open(self.paths['is_scraped'], 'r') as f:
                self.variables['is_scraped'] = json.load(f)

        self.paths['scraped_entryids'] = os.path.join(self.paths['processed_data'], "scraped_entryids.json")
        self.variables['scraped_entryids'] = {}
        if os.path.exists(self.paths['scraped_entryids']):
            with open(self.paths['scraped_entryids'], 'r') as f:
                self.variables['scraped_entryids'] = json.load(f)

        self.paths['entryids_path'] = os.path.join(self.paths['processed_data'], "entryids.json")
        self.variables['entryids'] = {}
        if os.path.exists(self.paths['entryids_path']):
            with open(self.paths['entryids_path'], 'r') as f:
                try:
                    self.variables['entryids'] = json.load(f)
                except:
                    raise ImportError('The < entryids.json > file is corrupted or empty.')
            
        self.paths['model_contents'] = os.path.join(self.paths['processed_data'], f'processed_{self.bigg_model_name}_model.json') 
        self.model_contents = {}       
        if os.path.exists(self.paths['model_contents']):
            with open(self.paths['model_contents'], 'r') as f:
                self.model_contents = json.load(f)        
        
        
    """
    --------------------------------------------------------------------
        STEP 1: SCRAPE SABIO WEBSITE BY DOWNLOAD XLS FOR GIVEN REACTIONS IN BIGG MODEL
    --------------------------------------------------------------------    
    """

    def _scrape_xls(self,reaction_identifier, search_option):
        self.driver.get("http://sabiork.h-its.org/newSearch/index")
       
        time.sleep(self.parameters['general_delay'])

        self._click_element_id("resetbtn")        
        
        time.sleep(self.parameters['general_delay'])
        
        self._click_element_id("option")
        self._select_dropdown_id("searchterms", search_option)
        text_area = self.driver.find_element_by_id("searchtermField")
        text_area.send_keys(reaction_identifier)  
        
        time.sleep(self.parameters['general_delay']) 
        
        self._click_element_id("addsearch")
        
        time.sleep(self.parameters['general_delay'])

        result_num = ""
        try: 
            result_num_ele = self.driver.find_element_by_id("numberofKinLaw")
            for char in result_num_ele.text:
                if re.search('[0-9]', char):
                    result_num = result_num + char

            result_num = int(result_num)
        except:
            #self.driver.close()
            self.driver.get("http://sabiork.h-its.org/newSearch/index")
            return False

        time.sleep(self.parameters['general_delay'])

        self._select_dropdown_id("max", "100")
        element = Select(self.driver.find_element_by_id("max"))
        element.select_by_visible_text("100")

        time.sleep(self.parameters['general_delay'])

        if result_num > 0 and result_num <= 100:
            self._click_element_id("allCheckbox")
            time.sleep(self.parameters['general_delay'])
        elif result_num > 100:
            self._click_element_id("allCheckbox")
            for i in range(int(result_num/100)):
                element = self.driver.find_element_by_xpath("//*[@class = 'nextLink']")
                element.click()
                time.sleep(self.parameters['general_delay'])
                self._click_element_id("allCheckbox")
                time.sleep(self.parameters['general_delay'])
        else:
            #self.driver.close()
            self.driver.get("http://sabiork.h-its.org/newSearch/index")
            return False

        self.driver.get("http://sabiork.h-its.org/newSearch/spreadsheetExport")
        
        time.sleep(self.parameters['general_delay']*7.5)
        
        element = self.driver.find_element_by_xpath("//*[text()[contains(., 'Add all')]]")
        element.click()
        
        time.sleep(self.parameters['general_delay']*2.5)
        
        self._click_element_id("excelExport")
        
        time.sleep(self.parameters['general_delay']*2.5)

        return True
    
#    def _expand_shadow_element(self, element):
#        shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', element)
#        return shadow_root
    
    def _split_reaction(self, 
                        reaction_string, # the sabio or bigg reaction string
                        sabio = False   # specifies how the reaction string will be split
                        ):
        def _parse_stoich(met):
            stoich = ''
            ch_number = 0
            denom = False
            numerator = denominator = 0
            while re.search('[0-9\./]', met[ch_number]): 
                stoich += met[ch_number]
                if met[ch_number] == '/':
                    numerator = stoich
                    denom = True
                if denom:
                    denominator += met[ch_number]
                ch_number += 1
                
            if denom:
                stoich = f'{numerator}/{denominator}'
            return stoich
        
        def met_parsing(met):
    #         print(met)
            met = met.strip()
            met = re.sub('_\w$', '', met)
            if re.search('(\d\s\w|\d\.\d\s|\d/\d\s)', met):
                coefficient = _parse_stoich(met)
                coefficient = '{} '.format(coefficient)
            else:
                coefficient = ''
            met = re.sub(coefficient, '', met)
    #         print(met, coefficient)
            return met, coefficient   
    
        def reformat_met_name(met_name, sabio = False):
            met_name = re.sub(' - ', '-', met_name)
            if not sabio:
                met_name = re.sub(' ', '_', met_name)
            return met_name
        
        def parsing_chemical_list(chemical_list):
            bigg_chemicals = []
            sabio_chemicals = []
            for met in chemical_list:
                if not re.search('[A-Za-z]', met):
                    continue
                met, coefficient = met_parsing(met)
                
                # assign the proper chemical names
                if not sabio:
                    sabio_chemicals.append(coefficient + reformat_met_name(self.bigg_to_sabio_metabolites[met]['name'], True))     
                    if 'bigg_name' in self.bigg_to_sabio_metabolites[met]:
                        bigg_chemicals.append(coefficient + reformat_met_name(self.bigg_to_sabio_metabolites[met]['bigg_name']))
                    else:
                        bigg_chemicals.append(coefficient + reformat_met_name(self.bigg_to_sabio_metabolites[met]['name']))
                elif sabio:
                    sabio_chemicals.append(coefficient + reformat_met_name(met, True))               
                    dic = CaseInsensitiveDict(self.sabio_to_bigg_metabolites)
                    if 'bigg_name' in dic.get(met):
                        bigg_chemicals.append(coefficient + reformat_met_name(dic.get(met)['bigg_name']))
                    else:
                        bigg_chemicals.append(coefficient + reformat_met_name(met))
            
            return bigg_chemicals, sabio_chemicals
        
            
        # parse the reactants and products for the specified reaction string
        if not sabio:
            reaction_split = reaction_string.split(' <-> ')
        else:
            reaction_split = reaction_string.split(' = ')
            
        reactants_list = reaction_split[0].split(' + ')
        products_list = reaction_split[1].split(' + ')
        
        # parse the reactants and products
        bigg_reactants, sabio_reactants = parsing_chemical_list(reactants_list)
        bigg_products, sabio_products = parsing_chemical_list(products_list)
        
        # assemble the chemicals list and reaction string
        bigg_compounds = bigg_reactants + bigg_products
        sabio_chemicals = sabio_reactants + sabio_products
        reactant_string = ' + '.join(bigg_reactants)
        product_string = ' + '.join(bigg_products)
        reaction_string = ' <-> '.join([reactant_string, product_string])
#        if sabio:
#            reaction_string = ' = '.join([reactant_string, product_string])        
        
        return reaction_string, sabio_chemicals, bigg_compounds
    
#    def _change_enzyme_name(self, enzyme):       #!!! TODO the scrapped XLS files must be named to the enzymes so that they can be distinguished in the folder, and imported and edited.
#        df_path = os.path.join(self.paths['raw_data'], enzyme)
#        with open(df_path) as xls:
#            df = pandas.read_xls(xls)
#            
#        df['Enzymename'] = [enzyme for name in len(df['Enzymename'])]
#        df.to_csv(df_path)

    def scrape_bigg_xls(self,):        
        # estimate the time to scrape the XLS files
        minutes_per_enzyme = 3*minute
        scraping_time = minutes_per_enzyme * len(self.model['reactions'])
        estimated_completion = datetime.datetime.now() + datetime.timedelta(seconds = scraping_time)     
        print(f'Estimated completion of scraping the XLS data for {self.bigg_model_name}: {estimated_completion}, in {scraping_time/hour} hours')
        
        # scrape SABIO data based upon various search parameters
        self.count = len(self.variables["is_scraped"])
        annotation_search_pairs = {"sabiork":"SabioReactionID", "metanetx.reaction":"MetaNetXReactionID", "ec-code":"ECNumber", "kegg.reaction":"KeggReactionID", "rhea":"RheaReactionID"}
        for enzyme in self.model['reactions']:
            # parse the reaction
            annotations = enzyme['annotation']
            enzyme_id = enzyme['id']
            enzyme_name = enzyme['name']
            
            og_reaction_string = self.bigg_reactions[enzyme_id]['reaction_string']
            reaction_string, sabio_chemicals, bigg_compounds = self._split_reaction(og_reaction_string)
            self.model_contents[enzyme_name] = {
                'reaction': {
                    'original': og_reaction_string,
                    'substituted': reaction_string,
                },
                'bigg_compounds': bigg_compounds,
                'sabio_chemicals': sabio_chemicals,
                'annotations': annotations
            }
    
            # search SABIO for reaction kinetics
            json_dict_key = enzyme_name.replace("\"", "")
            if not json_dict_key in self.variables['is_scraped']:
                annotation_search_pairs.update({
                        enzyme_name:"Enzymename"
                        })
#                self.variables['is_scraped'][json_dict_key] = False
#                while not success_flag:
                for database in annotation_search_pairs:
                    if database in annotations:
                        for ID in annotations[database]:
    #                                 success_flag = self._scrape_xls(ID, annotation_search_pairs[database])
                            try:
                                success_flag = self._scrape_xls(ID, annotation_search_pairs[database])
                                self.variables['is_scraped'][json_dict_key] = True
    #                                    self._change_enzyme_name(enzyme_name)
                            except:
                                if not success_flag:
                                    self.variables['is_scraped'][json_dict_key] = False
                                continue
                    
                self.count += 1
                print("\nReaction: " + str(self.count) + "/" + str(len(self.model['reactions'])), end='\r')
            else:
                print(f'< {enzyme_name} > was either already scraped, or is duplicated in the model.')

            # tracks scraping progress
            with open(self.paths['is_scraped'], 'w') as outfile:
                json.dump(self.variables['is_scraped'], outfile, indent = 4)   
                outfile.close()
                
        if self.export_model_content:
            with open(self.paths['model_contents'], 'w') as out:
                json.dump(self.model_contents, out, indent = 3)
                
        # update the step counter
        print(f'SABIO XLS data has been scraped.')
        self.step_number = 2
        self._progress_update(self.step_number)

    """
    --------------------------------------------------------------------
        STEP 2: GLOB EXPORTED XLS FILES TOGETHER
    --------------------------------------------------------------------
    """

    def glob_xls_files(self,):
#         scraped_sans_parentheses_enzymes = glob('./{}/*.xls'.format(self.paths['raw_data']))
        total_dataframes = []
        for file in glob(os.path.join(self.paths['raw_data'], '*.xls')):
            #file_name = os.path.splitext(os.path.basename(file))[0]
            dfn = pandas.read_excel(file)
            total_dataframes.append(dfn)

        # All scraped dataframes are combined and duplicate rows are removed
        combined_df = pandas.DataFrame()
        combined_df = pandas.concat(total_dataframes)
        combined_df = combined_df.fillna(' ')
        combined_df = combined_df.drop_duplicates()

        # export the dataframe
        self.paths['concatenated_data'] = os.path.join(self.paths['raw_data'], "00_concatenated_data.csv")
        combined_df.to_csv(self.paths['concatenated_data'])
        
        # update the step counter
        print(f'The XLS data has been concatenated.')
        self.step_number = 3
        self._progress_update(self.step_number)

    """
    --------------------------------------------------------------------
        STEP 3: SCRAPE ADDITIONAL DATA BY ENTRYID
    --------------------------------------------------------------------    
    """

    def _scrape_entry_id(self,entry_id):
        entry_id = str(entry_id)  
        self.driver.get("http://sabiork.h-its.org/newSearch/index")
        
        time.sleep(self.parameters['general_delay'])
        
        self._wait_for_id("resetbtn")
        
        time.sleep(self.parameters['general_delay'])
        
        self._click_element_id("resetbtn")
        
        time.sleep(self.parameters['general_delay']*2)

        self._click_element_id("option")
        self._select_dropdown_id("searchterms", "EntryID")
        text_area = self.driver.find_element_by_id("searchtermField")
        text_area.send_keys(entry_id)
        
        time.sleep(self.parameters['general_delay'])
        
        self._click_element_id("addsearch")
        
        time.sleep(self.parameters['general_delay'])
        
        self._click_element_id(entry_id + "img")
        
        time.sleep(self.parameters['general_delay'])
        
        self.driver.switch_to.frame(self.driver.find_element_by_xpath("//iframe[@name='iframe_" + entry_id + "']"))
        while True:
            try:
                element = self.driver.find_element_by_xpath("//table")                
                break
            except:
                time.sleep(self.parameters['general_delay'])

        element = self.driver.find_element_by_xpath("//table")
        html_source = element.get_attribute('innerHTML')
        table_df = pandas.read_html(html_source)
        reaction_parameters_df = pandas.DataFrame()
        counter = 0
        parameters_json = {}
        for df in table_df:
            try:
                if df[0][0] == "Parameter":
                    reaction_parameters_df = table_df[counter]
            except:
                self.driver.close()
                return parameters_json
            counter += 1
            
        for row in range(2, len(reaction_parameters_df[0])):
            parameter_name = str(reaction_parameters_df[0][row])
            inner_parameters_json = {}
            for col in range(1, len(reaction_parameters_df.columns)):
                parameter_type = str(reaction_parameters_df[col][1])
                inner_parameters_json[parameter_type] = reaction_parameters_df[col][row]

            parameters_json[parameter_name] = inner_parameters_json
        return parameters_json

    def scrape_entryids(self,):
        if 'concatenated_data' not in self.paths:
            self.paths['concatenated_data'] = os.path.join(self.paths['output_directory'], "00_concatenated_data.csv")
        
        self.sabio_df = pandas.read_csv(self.paths['concatenated_data'])
        entryids = self.sabio_df["EntryID"].unique().tolist()
        
        # estimate the time to scrape the the entryids
        minutes_per_enzyme = 2*minute
        scraping_time = minutes_per_enzyme * len(entryids)
        estimated_completion = datetime.datetime.now() + datetime.timedelta(seconds = scraping_time)          # approximately 1 minute per enzyme for Step 1
        print(f'Estimated completion of scraping the XLS data for {self.bigg_model_name}: {estimated_completion}, in {scraping_time/hour} hours')
        
        for entryid in entryids:
            if not str(entryid) in self.variables['entryids']:
                # only entries that possess calculable units will be processed and accepted
                self.variables['scraped_entryids'][str(entryid)] = "erroneous"
                parameters = self._scrape_entry_id(entryid)
                for param in parameters:
                    if not 'unit' in parameters[param]:
                        self.variables['scraped_entryids'][str(entryid)] = "missing_unit"
                    elif parameters[param]['unit'] == '-':
                        self.variables['scraped_entryids'][str(entryid)] = "missing_unit"
                    elif parameters[param]['start val.'] == '-' and parameters[param]['end val.'] == '-':
                        self.variables['scraped_entryids'][str(entryid)] = "missing_values"   
                    else:
                        self.variables['scraped_entryids'][str(entryid)] = "acceptable"
                        
                if self.variables['scraped_entryids'][str(entryid)] == 'acceptable':
                    self.variables['entryids'][str(entryid)] = parameters
                                    
                    with open(self.paths["scraped_entryids"], 'w') as outfile:
                        json.dump(self.variables['scraped_entryids'], outfile, indent = 4)   
                        outfile.close()
                    with open(self.paths["entryids_path"], 'w') as f:
                        json.dump(self.variables['entryids'], f, indent = 4)        
                        f.close()    
                else:
                    if self.verbose:
                        print(entryid, self.variables['scraped_entryids'][str(entryid)])
                        pprint(parameters[param])
                        
                print(f'Scraped entryID: {entryid}')
        
        # update the step counter
        print(f'The parameter specifications have been scraped.')
        self.step_number = 4
        self._progress_update(self.step_number)

    """
    --------------------------------------------------------------------
        STEP 4: COMBINE XLS AND ENTRYID DATA INTO A SINGLE JSON FILE
    --------------------------------------------------------------------
    """   
    
    def _determine_parameter_value(unit, original_value):
        # parse the unit
        numerator = ''
        denominator = ''
        term = ''
        skips = 0
        next_denominator = False
        for index in range(len(unit)):
            if skips > 0:
                skips -= 1 
                continue
                
            ch = unit[index]
            term += ch
            
            # parse the unit characters
            if len(unit) == 1:
                numerator += term
                term = ''
                break
            if index+1 == len(unit)-1:
                if next_denominator:
                    denominator += term
                    denominator += unit[index+1]
                else:
                    numerator += term
                    numerator += unit[index+1]
                term = ''
                break
            if unit[index+1] == '^':
                if unit[index+2:index+6] == '(-1)':
                    denominator += term 
                    skips = 5
                    term = ''
                else:
                    print(unit, term)
            elif unit[index+1] == '/':
                numerator += term
                term = ''
                skips = 1
                next_denominator = True
                
        if term != '':
            print(unit, term)
        unit_dic = {
            'numerator':numerator,
            'denominator': denominator
        }
        
        # determine the mathematically equivalent value in base units
        value = original_value
        for group in unit_dic:
            term = unit_dic[group]
            if re.search('min', unit_dic[group]):
                if group == 'numerator':
                    value *= minute
                    unit_dic[group] = re.sub('min', 's', unit_dic[group])
                else:
                    value /= minute  
                    unit_dic[group] = re.sub('min', 's', unit_dic[group])
            if re.search('mg|mM|mmol', unit_dic[group]):
                if group == 'numerator':
                    value *= milli
                    unit_dic[group] = re.sub('m', '', unit_dic[group], count = 1)
                else:
                    value /= milli    
                    unit_dic[group] = re.sub('m', '', unit_dic[group])
            if re.search('ng|nM|nmol', unit_dic[group]):
                if group == 'numerator':
                    value *= nano
                    unit_dic[group] = re.sub('n', '', unit_dic[group])
                else:
                    value /= nano   
                    unit_dic[group] = re.sub('n', '', unit_dic[group])
            if re.search('µ|u00b5|U\+00B5', unit_dic[group]):
                if group == 'numerator':
                    value *= micro
                    unit_dic[group] = re.sub('µ|u00b5g|U\+00B5', '', unit_dic[group])
                else:
                    value /= micro 
                    unit_dic[group] = re.sub('µ|u00b5g|U\+00B5', '', unit_dic[group])
                                    
        return value, unit_dic
    
    def _parameter_value(self, var, parameter_info):
        # determine the average parameter value
        end_value = start_value = None
        for start in ["start val.","start value", ]:
            if start in parameter_info[var]:
                start_value = parameter_info[var][start]
                break
        for end in ["end val.","end value", ]:    
            if end in parameter_info[var]:
                end_value = parameter_info[var][end]                                
                break
            
        return average(start_value, end_value)

    def to_fba(self,):
        # import previously parsed content
        with open(self.paths['entryids_path']) as json_file: 
            entry_id_data_file = json.load(json_file)
            
        try:
            if self.sabio_df:
                pass
            else:
                self.sabio_df = pandas.read_csv(self.paths['concatenated_data'])
        except:
            self.sabio_df = pandas.read_csv(self.paths['concatenated_data'])

        # combine the scraped data into a programmable JSON  
        enzyme_dict = {}
        missing_entry_ids = []
        enzymes = self.sabio_df["Enzymename"].unique().tolist()
        for enzyme in enzymes:
            enzyme_df = self.sabio_df.loc[self.sabio_df["Enzymename"] == enzyme]
            enzyme_dict[enzyme] = {}
            reactions = enzyme_df["Reaction"].unique().tolist()
            for reaction in reactions:
                enzyme_dict[enzyme][reaction] = {}
                
                # ensure that the reaction chemicals match before accepting kinetic data
                print('reaction', reaction)
                rxn_string, sabio_chemicals, expected_bigg_chemicals = self._split_reaction(reaction, sabio = True)
                bigg_chemicals = self.model_contents[enzyme]['chemicals']
                
                extra_bigg = set(bigg_chemicals) - set(expected_bigg_chemicals) 
                extra_bigg = set(re.sub('(H\+|H2O)', '', chem) for chem in extra_bigg)           
                if len(extra_bigg) != 1 and extra_bigg[0] != '':
                    missed_reaction = f'The || {rxn_string} || reaction with {expected_bigg_chemicals} chemicals does not match the BiGG reaction of {bigg_chemicals} chemicals.'
                    if self.printing:
                        print(missed_reaction)
                    enzyme_dict[enzyme][reaction] = missed_reaction
                    continue
                
                # parse and filter each entryid of the matching reaction
                enzyme_reactions_df = enzyme_df.loc[enzyme_df["Reaction"] == reaction]
                entryids = enzyme_reactions_df["EntryID"].unique().tolist()
                for entryid in entryids:
                    entryid = str(entryid)
                    entry_id_row = enzyme_reactions_df.loc[enzyme_reactions_df["EntryID"] == entryid]
                    head_of_df = entry_id_row.head(1).squeeze()
                    
                    # assign the rate law for an entryid
                    rate_law = head_of_df["Rate Equation"]
                    if not rate_law in ["unknown", "", "-"]:                    
                        enzyme_dict[enzyme][reaction][entryid_string]["RateLaw"] = rate_law
                    else:
                        continue
                    
                    # define the parameters for extant entryids
                    enzyme_dict[enzyme][reaction][entryid] = {}
                    if entryid in entry_id_data_file:                        
                        # rename "species" -> "chemical"
                        enzyme_dict[enzyme][reaction][entryid] = entry_id_data_file[entryid]
                        parameters = []
                        for param in entry_id_data_file[entryid]:
                            enzyme_dict[enzyme][reaction][entryid]["Parameters"][param]['chemical'] = entry_id_data_file[entryid][param]['species']
                            enzyme_dict[enzyme][reaction][entryid]["Parameters"][param].pop('species')
                            parameters.append(param)
                    else:
                        missing_entry_ids.append(entryid)
                        continue

                    # add annotations and metadata to the assembled dictionary
                    annotations = {}
                    for annotation in ["SabioReactionID", "PubMedID", 'ECNumber', 'KeggReactionID']:
                        annotations[annotation] = head_of_df[annotation]
                    enzyme_dict[enzyme][reaction][entryid]['annotations'] = annotations
                    
                    metadata = {}
                    for field in ["Buffer", "Product", "Publication", "pH", "Temperature", "Enzyme Variant", "KineticMechanismType", "Organism", "Pathway", ]:  
                        metadata[field] = head_of_df[field]
                    enzyme_dict[enzyme][reaction][entryid]['metadata'] = metadata
                        
                    # substitute quantities into the rate law 
                    stripped_string = re.sub('[0-9]', '', rate_law)
                    variables = re.split("[^*+-/() ]", stripped_string)   #!!! This logic for determining the set of variables in the rate law must be verified.
                    variables = ' '.join(variables).split()
                    
                    substituted_parameters = {}
                    variable_molar = {}
                    variable_name = {}
                    parameter_info = {}
                    parameter_value = True
                    while parameter_value:
                        for var in variables:
                            # the acceptable variables are filtered for those that possess data and those that are substrates
                            if var in entry_id_data_file[entryid]:
                                if parameters[var]['type'] == 'concentration':
                                    variable_name[var] = enzyme_dict[enzyme][reaction][entryid]["Parameters"][var]['chemical']
                                    parameter_value = self._parameter_value(var, parameter_info)                                                                       
                                    unit = parameter_info[var]['unit']
                                    parameter_value, unit_dict = self._determine_parameter_value(unit, parameter_value)
                                    
                                    if len(var) == 1 and var != 'E':
                                        if not parameter_value:
                                            parameter_value = False
                                            break
                                        substituted_rate_law = rate_law.replace(var, parameter_value)
                                        substituted_parameters[var] = entry_id_data_file[entryid][var]
                                    else:
                                        variable_molar[var] = parameter_value

                        # define the final JSON with the desired content and organization
                        enzyme_dict[enzyme][reaction][entryid]["substituted_rate_law"] = substituted_rate_law
                        enzyme_dict[enzyme][reaction][entryid]["substituted_parameters"] = substituted_parameters
                        enzyme_dict[enzyme][reaction][entryid]["variables_molar"] = variable_molar
                        enzyme_dict[enzyme][reaction][entryid]["variables_name"] = variable_name
                        
                        defined_content = variable_molar + substituted_parameters
                        if defined_content != parameters:
                            print('---> ERROR: The rate rate {rate_law} does not reflect all of the defined variables and parameters by the entry: {defined_content}.')
                        enzyme_dict[enzyme][reaction][entryid].pop('Parameters')
                        
                        parameter_value = False
                    
                    # remove entryids whose rate laws could not be completely substituted, and thus are not calculable
                    if not "SubstitutedRateLaw" in enzyme_dict[enzyme][reaction][entryid]:
                        enzyme_dict[enzyme][reaction].pop(entryid)

        with open(self.paths["scraped_model_path"], 'w', encoding="utf-8") as f:
            json.dump(enzyme_dict, f, indent=4, sort_keys=True, separators=(', ', ': '), ensure_ascii=False, cls=NumpyEncoder)
            
        # update the step counter
        print(f'The dFBA data file have been generated.')
        self.step_number = 5
        self._progress_update(self.step_number)
        
        
    def _progress_update(self, step):
        if not re.search('[0-5]', str(step)):
            print(f'--> ERROR: The {step} step is not acceptable.')
        f = open(self.paths['progress_path'], "w")
        f.write(str(step))
        f.close()

    def main(self,                               #!!! arguments must be added to the individual functions to promote modularity of the script and thus more use-cases
             ):
        self.start()

        # commence the browser
        self.fp = webdriver.FirefoxProfile(os.path.join(self.paths['root_path'],"l2pnahxq.scraper"))
        self.fp.set_preference("browser.download.folderList", 2)
        self.fp.set_preference("browser.download.manager.showWhenStarting", False)
        self.fp.set_preference("browser.download.dir", self.paths["raw_data"])
        self.fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")
        self.driver = webdriver.Firefox(firefox_profile=self.fp, executable_path=os.path.join(self.paths['root_path'],"geckodriver.exe"))
        self.driver.get("http://sabiork.h-its.org/newSearch/index")

        while True:
            if self.step_number == 1:
                self.scrape_bigg_xls()
            elif self.step_number == 2:
                self.glob_xls_files()
            elif self.step_number == 3:
                self.scrape_entryids()
            elif self.step_number == 4:
                self.to_fba()
            elif self.step_number == 5:
                print("Execution complete. Scraper finished.")
                rmtree(self.paths['progress_path'])
                break
            
#scraping = SABIO_scraping()
#scraping.main('../bigg_models/Ecoli core, BiGG, indented.json', 'test_Ecoli')
##print(scraping.)