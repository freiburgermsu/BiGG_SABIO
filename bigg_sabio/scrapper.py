# -*- coding: utf-8 -*-
"""
@authors: Ethan Sean Chan, Andrew Philip Freiburger
"""
from scipy.constants import minute, hour
from selenium.webdriver.support.ui import Select
from selenium import webdriver
from shutil import rmtree
from glob import glob
import numpy as np
import datetime
import pandas
import json, time, re, os

#Taken from: https://github.com/hmallen/numpyencoder
class NumpyEncoder(json.JSONEncoder):
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
                 export_content: bool = False):
        self.export_content = export_content 
        self.count = 0
        self.paths = {}
        
        self.parameters = {}
        self.parameters['general_delay'] = 2
        
        self.variables = {}
        
        # load BiGG model content 
        self.bigg_to_sabio_metabolites = json.load(open('BiGG_metabolites, parsed.json'))
        self.sabio_to_bigg_metabolites = json.load(open('BiGG_metabolite_names, parsed.json'))
        self.bigg_reactions = json.load(open('BiGG_reactions, parsed.json'))

    #Clicks a HTML element with selenium by id
    def _click_element_id(self,n_id):
        element = self.driver.find_element_by_id(n_id)
        element.click()
        time.sleep(self.parameters['general_delay'])
        
    def _wait_for_id(self,n_id):
        while True:
            try:
                element = self.driver.find_element_by_id(n_id)   # what is the purpose of this catch?
                break
            except:
                time.sleep(self.parameters['general_delay'])
        

    #Selects a choice from a HTML dropdown element with selenium by id
    def _select_dropdown_id(self,n_id, n_choice):
        element = Select(self.driver.find_element_by_id(n_id))
        element.select_by_visible_text(n_choice)
        time.sleep(self.parameters['general_delay'])

    def _fatal_error_handler(self,message):
        print("Error: " + message)
        print("Exiting now...")
        exit(0)

    """
    --------------------------------------------------------------------
        STEP 0: GET BIGG MODEL TO SCRAPE AND SETUP DIRECTORIES AND PROGRESS FILE
    --------------------------------------------------------------------    
    """

    def start(self,
              bigg_model_path:str,  # the JSON version of the BiGG model
              bigg_model_name:str   # the name of the BiGG model
              ): 
        
        if os.path.exists(bigg_model_path):
            self.model = json.load(open(bigg_model_path))
        else:
            self._fatal_error_handler('The BiGG model file does not exist')
            
        self.bigg_model_name = bigg_model_name 
        if bigg_model_name is None:
            self.bigg_model_name = re.search("([\w+\.?\s?]+)(?=\.json)", bigg_model_path).group()

        # define core paths
        self.paths['cwd'] = os.path.dirname(os.path.realpath(bigg_model_path))
        self.paths['output_directory'] = os.path.join(self.paths['cwd'],f"scraping-{self.bigg_model_name}")       
        self.paths['scraped_model_path'] = os.path.join(self.paths['output_directory'], "scraped_model.json")
        
        if not os.path.isdir(self.paths['output_directory']):        
            os.mkdir(self.paths['output_directory'])
                    
        # monitor the scrapping progress
        self.paths['progress_path'] = os.path.join(self.paths['output_directory'], "current_progress.txt")
        if os.path.exists(self.paths['progress_path']):
            with open(self.paths['progress_path'], "r") as f:
                self.step_number = int(f.read(1))
                if not re.search('[1-5]',str(self.step_number)):
                    self._fatal_error_handler("Progress file malformed. Create a < current_progress.txt > file with a < 1-5 > digit to signify the current scrapping progress.")
        else:
            self.step_number = 1
            self._progress_update(self.step_number)

        # define the data directories
        self.paths['raw_data'] = os.path.join(self.paths['output_directory'], 'downloaded_xls') 
        if not os.path.isdir(self.paths['raw_data']):
            os.mkdir(self.paths['raw_data'])

        self.paths['processed_data'] = os.path.join(self.paths['output_directory'], 'processed_data') 
        if not os.path.isdir(self.paths['processed_data']):
            os.mkdir(self.paths['processed_data'])

        # define file paths and import content from an interupted scrapping        
        self.paths['is_scraped'] = os.path.join(self.paths['output_directory'], self.paths['raw_data'], "is_scraped.json")
        self.variables['is_scraped'] = {}
        if os.path.exists(self.paths['is_scraped']):
            with open(self.paths['is_scraped'], 'r') as f:
                self.variables['is_scraped'] = json.load(f)

        self.paths['scraped_entryids'] = os.path.join(self.paths['output_directory'], self.paths['processed_data'], "scraped_entryids.json")
        self.variables['scraped_entryids'] = {}
        if os.path.exists(self.paths['scraped_entryids']):
            with open(self.paths['scraped_entryids'], 'r') as f:
                self.variables['scraped_entryids'] = json.load(f)

        self.paths['entryids_path'] = os.path.join(self.paths['output_directory'], self.paths['processed_data'], "entryids.json")
        self.variables['entryids'] = {}
        if os.path.exists(self.paths['entryids_path']):
            f = open(self.paths[''], "r")
            with open(self.paths['entryids_path'], 'r') as f:
                try:
                    self.variables['entryids'] = json.load(f)
                except:
                    self._fatal_error_handler('-> ERROR: The < entryids.json > file is corrupted or empty.')
            
        self.paths['model_contents'] = os.path.join(self.paths['output_directory'], self.paths['processed_data'], f'processed_{self.bigg_model_name}_model.json') 
        self.model_contents = {}       
        if os.path.exists(self.paths['model_contents']):
            with open(self.paths['model_contents'], 'r') as f:
                self.model_contents = json.load(f)
        
    """
    --------------------------------------------------------------------
        STEP 1: SCRAPE SABIO WEBSITE BY DOWNLOAD XLS FOR GIVEN REACTIONS IN BIGG MODEL
    --------------------------------------------------------------------    
    """

    def scrape_xls(self,reaction_identifier, search_option):
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
    
    def _change_enzyme_name(self, enzyme):       # the scrapped XLS files must be named to the enzymes so that they can be distinguished in the folder, and imported and edited.
        df_path = os.path.join(self.paths['raw_data'], enzyme)
        with open(df_path) as xls:
            df = pandas.read_xls(xls)
            
        df['Enzymename'] = [enzyme for name in len(df['Enzymename'])]
        df.to_csv(df_path)

    def scrape_bigg_xls(self,):        
        # estimate the completion time
        minutes_per_enzyme = 3
        reactions_quantity = len(self.model['reactions'])
        estimated_time = reactions_quantity*minutes_per_enzyme*minute
        estimated_completion = datetime.datetime.now() + datetime.timedelta(seconds = estimated_time)
        print(f'Estimated completion of scraping data for {self.bigg_model_name}): {estimated_completion}, in {estimated_time/hour} hours')

        self.count = len(self.variables["is_scraped"])
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
            if not enzyme_name in self.variables['is_scraped']:
                success_flag = False
                annotation_search_pairs = {"sabiork":"SabioReactionID", "metanetx.reaction":"MetaNetXReactionID", "ec-code":"ECNumber", "kegg.reaction":"KeggReactionID", "rhea":"RheaReactionID"}
                for database in annotation_search_pairs:
                    if not success_flag:
                        if database in annotations:
                            for ID in annotations[database]:
#                                 success_flag = self.scrape_xls(ID, annotation_search_pairs[database])
                                try:
                                    success_flag = self.scrape_xls(ID, annotation_search_pairs[database])
                                except:
                                    success_flag = False
                    else:
                        break

                if not success_flag:
                    try:
                        success_flag = self.scrape_xls(enzyme_name, "Enzymename")
                        self._change_enzyme_name(enzyme_name)
                    except:
                        success_flag = False

                json_dict_key = enzyme_name.replace("\"", "")
                if success_flag:
                    self.variables['is_scraped'][json_dict_key] = "yes"
                else:
                    self.variables['is_scraped'][json_dict_key] = "no"
                    
                self.count += 1
                print("\nReaction: " + str(self.count) + "/" + str(len(self.model['reactions'])), end='\r')

            with open(self.paths['is_scraped'], 'w') as outfile:
                json.dump(self.variables['is_scraped'], outfile, indent = 4)   
                outfile.close()
                
        if self.export_content:
            with open(, 'w') as out:
                json.dump(self.model_contents, out, indent = 3)
                
        # update the step counter
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
        self.step_number = 3
        self._progress_update(self.step_number)

    """
    --------------------------------------------------------------------
        STEP 3: SCRAPE ADDITIONAL DATA BY ENTRYID
    --------------------------------------------------------------------    
    """

    def _scrape_entry_id(self,entry_id):
        entry_id = str(entry_id)
        self.driver = webdriver.Firefox(firefox_profile=self.fp, executable_path="geckodriver.exe")         
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
            self.paths['concatenated_data'] = os.path.join(self.paths['output_directory'], "proccessed-xls.csv")
        
        self.sabio_df = pandas.read_csv(self.paths['concatenated_data'])
        entryids = self.sabio_df["EntryID"].unique().tolist()
        for entryid in entryids:
            if not str(entryid) in self.variables['entryids']:
                self.variables['entryids'][str(entryid)] = self._scrape_entry_id(entryid)
                self.variables['scraped_entryids'][str(entryid)] = "yes"
            with open(self.paths["scraped_entryids"], 'w') as outfile:
                json.dump(self.variables['scraped_entryids'], outfile, indent = 4)   
                outfile.close()
            with open(self.paths["entryids_path"], 'w') as f:
                json.dump(self.variables['entryids'], f, indent = 4)        
                f.close()
        
        # update the step counter
        self.step_number = 4
        self._progress_update(self.step_number)

    """
    --------------------------------------------------------------------
        STEP 4: COMBINE XLS AND ENTRYID DATA INTO A SINGLE JSON FILE
    --------------------------------------------------------------------
    """   

    def combine_data(self,):
        # import previously parsed content
        with open(self.paths['entryids_path']) as json_file: 
            entry_id_data = json.load(json_file)
            
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
                rxn_string, sabio_chemicals, expected_bigg_chemicals= self._split_reaction(reaction, sabio = True)
                bigg_chemicals = self.model_contents[enzyme]['chemicals']
                
                extra_bigg = set(bigg_chemicals) - set(expected_bigg_chemicals) 
                extra_bigg = set(re.sub('(H\+|H2O)', '', chem) for chem in extra_bigg)           
                if len(extra_bigg) != 1 and extra_bigg[0] = '':
                    missed_reaction = f'The || {rxn_string} || reaction with {expected_bigg_chemicals} chemicals does not match the BiGG reaction of {bigg_chemicals} chemicals.'
                    if self.printing:
                        print(missed_reaction)
                    enzyme_dict[enzyme][reaction] = missed_reaction
                    continue
                
                # parse each entryid of each reaction
                enzyme_reactions_df = enzyme_df.loc[enzyme_df["Reaction"] == reaction]
                entryids = enzyme_reactions_df["EntryID"].unique().tolist()
                for entryid in entryids:
                    enzyme_reaction_entryids_df = enzyme_reactions_df.loc[enzyme_reactions_df["EntryID"] == entryid]
                    entryid_string = f'condition_{entryid}'
                    enzyme_dict[enzyme][reaction][entryid_string] = {}
                    head_of_df = enzyme_reaction_entryids_df.head(1).squeeze()
                    entry_id_flag = True
                    parameter_info = {}

                    try:
                        parameter_info = entry_id_data[str(entryid)]
                        enzyme_dict[enzyme][reaction][entryid_string]["Parameters"] = parameter_info
                    except:
                        missing_entry_ids.append(str(entryid))
                        entry_id_flag = False
                        enzyme_dict[enzyme][reaction][entryid_string]["Parameters"] = "NaN"

                    rate_law = head_of_df["Rate Equation"]
                    bad_rate_laws = ["unknown", "", "-"]

                    if not rate_law in bad_rate_laws:                    
                        enzyme_dict[enzyme][reaction][entryid_string]["RateLaw"] = rate_law
                        enzyme_dict[enzyme][reaction][entryid_string]["SubstitutedRateLaw"] = rate_law
                    else:
                        enzyme_dict[enzyme][reaction][entryid_string]["RateLaw"] = "NaN"
                        enzyme_dict[enzyme][reaction][entryid_string]["SubstitutedRateLaw"] = "NaN"

                    if entry_id_flag:
                        fields_to_copy = ["Buffer", "Product", "PubMedID", "Publication", "pH", "Temperature", "Enzyme Variant", "UniProtKB_AC", "Organism", "KineticMechanismType", "SabioReactionID"]
                        for field in fields_to_copy:  
                            enzyme_dict[enzyme][reaction][entryid_string][field] = head_of_df[field]
                            
                        enzyme_dict[enzyme][reaction][entryid_string]["Substrates"] = head_of_df["Substrate"].split(";")
                        out_rate_law = rate_law
                        if not rate_law in bad_rate_laws:                    
                            substrates = head_of_df["Substrate"].split(";")

                            stripped_string = re.sub('[0-9]', '', rate_law)

                            variables = re.split("\^|\*|\+|\-|\/|\(|\)| ", stripped_string)
                            variables = ' '.join(variables).split()

                            start_value_permutations = ["start value", "start val."]
                            substrates_key = {}
                            for var in variables:
                                if var in parameter_info:
                                    for permutation in start_value_permutations:
                                        try:
                                            if var == "A" or var == "B":
                                                substrates_key[var] = parameter_info[var]["species"]
                                            else:
                                                value = parameter_info[var][permutation]
                                                if value != "-" and value != "" and value != " ":           # The quantities must be converted to base units
                                                    out_rate_law = out_rate_law.replace(var, parameter_info[var][permutation])
                                        except:
                                            pass

                            enzyme_dict[enzyme][reaction][entryid_string]["RateLawSubstrates"] = substrates_key
                            enzyme_dict[enzyme][reaction][entryid_string]["SubstitutedRateLaw"] = out_rate_law

        with open(self.paths["scraped_model_path"], 'w', encoding="utf-8") as f:
            json.dump(enzyme_dict, f, indent=4, sort_keys=True, separators=(', ', ': '), ensure_ascii=False, cls=NumpyEncoder)
            
        # update the step counter
        self.step_number = 5
        self._progress_update(self.step_number)
        
        
    def _progress_update(self, step):
        if not re.search('[0-5]', str(step)):
            print(f'--> ERROR: The {step} step is not acceptable.')
        f = open(self.paths['progress_path'], "w")
        f.write(str(step))
        f.close()

    def main(self,
             bigg_model_path: dict,
             bigg_model_name: str = None
             ):
        self.start(bigg_model_path, bigg_model_name)

        # commence the browser
        self.fp = webdriver.FirefoxProfile("l2pnahxq.scraper")
        self.fp.set_preference("browser.download.folderList", 2)
        self.fp.set_preference("browser.download.manager.showWhenStarting", False)
        self.fp.set_preference("browser.download.dir", self.paths["raw_data"])
        self.fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")
        self.driver = webdriver.Firefox(firefox_profile=self.fp, executable_path="geckodriver.exe")
        self.driver.get("http://sabiork.h-its.org/newSearch/index")

        while True:
            if self.step_number == 1:
                self.scrape_bigg_xls()
            elif self.step_number == 2:
                self.glob_xls_files()
            elif self.step_number == 3:
                self.scrape_entryids()
            elif self.step_number == 4:
                self.combine_data()
            elif self.step_number == 5:
                print("Execution complete. Scraper finished.")
                rmtree(self.paths['progress_path'])
                break
            
scraping = SABIO_scraping()
scraping.main('Ecoli core, BiGG, indented.json', 'test_Ecoli')