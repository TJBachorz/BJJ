import pandas as pd
import os
from nltk.corpus import stopwords
sw = stopwords.words("english")
from Functions.functions import dictionary_processing

path = os.getcwd()

############################################################################## 
# getting the data and deleting unimportant columns
data = pd.read_csv(path + r'\BJJ1.csv')

data = data.drop(columns = ['RecipientEmail','RecipientFirstName',
                            'RecipientLastName','IPAddress',
                            'ExternalReference', 'DistributionChannel'])

data = data.fillna('no answer')

# creating a dictionaty for future column names mapping
colnames = data[:][:1].values.tolist()[0]
colnames_dict = dict(zip(list(data), colnames))

# final dataset with questions only
qestions_order = sorted(list(data)[8:], key = lambda x: float(x[1:]))

data = data[:][2:]
data = data[data['Progress'].astype(int) > 10]

data_q = data[qestions_order][2:]

########################## age categories ####################################
from Functions.functions import age_categories
    
data_q['age_cat'] = data_q['Q57'].apply(age_categories)  

############ corrected case so it's consistent with other values #############

data_q['Q2'] = data_q['Q2'].apply(lambda x: x.lower())
data_q['Q2'][data_q['Q2'] == 'i do not hold a rank'] = 'no rank' 

##########################  nationality  #####################################

from Dictionaries.country_dictionary import country_dictionary
#from Functions.functions import explode

data_dem = dictionary_processing(
               data = data_q, 
               chosen_columns = ['Q67'],
               check = '(@[A-Za-z]+)|([^A-Za-z \t\&])|(\w+:\/\/\S+)',
               list_replacements = [['.',''],['new ','new'], \
                                    ['south ','south']], 
               dictionary = country_dictionary,
               new_names = ['countries'])
  
data_q = data_q.join(data_dem[['countries']])

data_q['country'] = data_q['countries'].apply(lambda x: x[0])

#data_q = explode(data_q, 'countries', 'country')

############################  athletes  ######################################

from Dictionaries.athlete_dictionary import athlete_dictionary 

data_athletes = dictionary_processing(
               data = data_q, 
               chosen_columns = ['Q63'],
               check = '(@[A-Za-z]+)|([^A-Za-z])|(\w+:\/\/\S+)',
               list_replacements = [['\'s',''],['.',','],['/',','],\
                                    [' and ',','],['&',','],[';',','], \
                                    ['!',','],['-',',']], 
               dictionary = athlete_dictionary,
               new_names = ['athletes'])

##########################  submissions  #####################################

from Dictionaries.submissions_dictionary import submissions_dictionary 

data_submissions = dictionary_processing(
                       data = data_q, 
                       chosen_columns = ['Q68'],
                       check = \
                          '(@[A-Za-z0-9]+)|([^A-Za-z0-9 \t\&])|(\w+:\/\/\S+)',
                       list_replacements = [['\'',''],[' & ','&']], 
                       dictionary = submissions_dictionary,
                       new_names = ['technique'])


from Functions.functions import is_choke

data_submissions['choke'] = data_submissions['technique']. \
                                            apply(lambda x: is_choke(x))

######################   Gi & NoGi favourite brands  #########################

from Dictionaries.gi_dictionary import gi_dictionary

data_gi = dictionary_processing(
                data = data_q,         
                chosen_columns = ["Q39","Q40","Q41","Q43"],
                check = '(@[A-Za-z0-9]+)|([^A-Za-z0-9 \t\&])|(\w+:\/\/\S+)',
                list_replacements = [['\'',''],[' & ','&']], 
                dictionary = gi_dictionary,
                new_names = ['gi','rash','shorts','apparel'])

################## BJJ academies and affiliations ############################

from Dictionaries.academy_dictionary import academy_dictionary

data_gyms = dictionary_processing(
                data = data_q, 
                chosen_columns = ["Q66"] ,
                check = '(@[A-Za-z0-9]+)|([^A-Za-z0-9])|(\w+:\/\/\S+)',
                list_replacements = [['&',','],['-',','],['/',','],['(',',']], 
                dictionary = academy_dictionary,
                new_names = ['gym'])

######################   Podcasts / YT channels ...  #########################

from Dictionaries.media_dictionary import media_dictionary

data_podcasts = dictionary_processing(
                data = data_q, 
                chosen_columns = ["Q50","Q61.1","Q65"] ,
                check = '(@[A-Za-z0-9]+)|([^A-Za-z0-9 \t/])|(\w+:\/\/\S+)',
                list_replacements = [['\'',''],[' & ',','],['www.',','], \
                                     [' and ',','],['. ',','],['.com',',']], 
                dictionary = media_dictionary,
                new_names = ['website','watch_sport','podcast'])

###############################   injuries  ##################################

from Dictionaries.injuries_dictionary import injuries_dictionary

data_injuries = dictionary_processing(
                data = data_q, 
                chosen_columns = ["Q28"] ,
                check = '(@[A-Za-z]+)|([^A-Za-z])|(\w+:\/\/\S+)',
                list_replacements = [['\'s','']], 
                dictionary = injuries_dictionary,
                new_names = ['injuries'])

############################   organisations  ################################

from Dictionaries.organisation_dictionary import organisation_dictionary

data_org = dictionary_processing(
                data = data_q, 
                chosen_columns = ["Q26"] ,
                check = '(@[A-Za-z0-9]+)|([^A-Za-z0-9])|(\w+:\/\/\S+)',
                list_replacements = [['\'s',''],['-',' ']], 
                dictionary = organisation_dictionary,
                new_names = ['organisations'])  

######################## reasons why you started #############################

from Dictionaries.reasons_dictionary import reasons_dictionary
from Functions.functions import find_dict_vals

data_q['reasons'] = data_q['Q18'].apply(lambda x: \
                                      find_dict_vals(x, reasons_dictionary))

##################### least favourite thing about BJJ ########################

from Dictionaries.least_fav_dictionary import least_fav_dictionary

data_q['least_favourite'] = data_q['Q20'].apply(lambda x: \
                                      find_dict_vals(x, least_fav_dictionary))

############### combining all the proseccessed datasets into one #############

list_datasets = [data_athletes, data_submissions, data_gi,data_gyms, \
                 data_podcasts, data_injuries, data_org]

data_q = data_q.join([dataset for dataset in list_datasets])
    
######################## renaming the columns ################################

from Dictionaries.colnames_dictionary import colnames_dictionary

data_qf = data_q.rename(columns = colnames_dictionary)        

data_final = data_qf[[x for x in list(data_qf) if 'Q' not in x]]

########### final data cleaning - change list to string #####################
to_str_columns =   ['countries',
                    'reasons',
                    'least_favourite',
                    'athletes',
                    'technique',
                    'gi',
                    'rash',
                    'shorts',
                    'apparel',
                    'gym',
                    'website',
                    'watch_sport',
                    'podcast',
                    'injuries',
                    'organisations']

for column in to_str_columns:
    data_final[column] = data_final[column].apply(lambda x: '['+','.join(x)+']')


data_final.to_csv(path + r'\Data\data_bjj.csv', header = True, index = None, 
                  sep = ';')

######################### interesting raw data ###############################

from Dictionaries.colnames_dictionary import raw_colnames

data_raw = data[raw_colnames.keys()][2:].rename(columns = raw_colnames)        

data_raw.to_csv(path + r'\Data\data_raw.csv', header = True, index = None, 
                  sep = ';')

#%%

base = ['current_belt','gender']    

training_info = ['training_years',
                 'white_blue',
                 'blue_purple',
                 'purple_brown',
                 'brown_black',
                 'training_per_week',
                 'both_gi_nogi',
                 'gi_or_no_gi',
                 'training_time',
                 'travel',
                 'background_ma',
                 'how_old_when_started',
                 'currently_cross_train',
                 'mobility_exercises',
                 'yoga',
                 'preferred_style',
                 'have_fav_athlete',
                 'leg_lock_friendly',
                 'gym_self_defense',
                 'membership',
                 #'gym', 
                 'gym_curriculum',
                 'time_watching_bjj',
                 'do_watch_sport_bjj',
                 'num_gis',
                 'num_rashguards',
                 'num_shorts',
                 'bjj_apparel',
                 'money_for_gear',
                 'education',
                 'income',
                 'age',
                 'age_cat',
                 'race', 
                 'nationality',
                 'country',
                 'instrutor_encourages_competition',
                 'competed',
                 'medals'
                 #'competition_organisaiton',
                 ]

reasons_info = ['reasons']

least_f_info = ['least_favourite']

subs_info = ['choke','technique']
 
injury_info = ['injuries']

athlete_info = ['athletes']

watch_info = ['watch_sport']

podcast_info = ['podcast']

web_info = ['website']

gi_info = ['gi']
rash_info = ['rash']
shorts_info = ['shorts']
apparel_info = ['apparel']

comp_info =  ['organisations']


dataset_list = [training_info, injury_info, athlete_info, watch_info]

dataset_names = ["training_info", "injury_info", "athlete_info", 
                 "watch_info"]

to_explode = [reasons_info, least_f_info, subs_info, podcast_info, web_info, 
              gi_info, rash_info, shorts_info, apparel_info, comp_info]

explode_names = ["reasons_info", "least_f_info", "subs_info", "podcast_info", 
                 "web_info", "gi_info", "rash_info", "shorts_info", 
                 "apparel_info", "comp_info"]

#%%
for dataset, name in zip(dataset_list, dataset_names):
    
    data_save = data_final[base + dataset]
    data_save.to_csv(path + r'\Data\info\{}.csv'.format(name), header = True, 
                   index = None, sep = ';')
    
#%%   
from Functions.functions import explode    
 
for dataset, name in zip(to_explode, explode_names):    
    
    data_save = data_final[base + dataset]
    var_to_expl = dataset[-1]
    
    data_save = explode(data_save, var_to_expl, var_to_expl)
    
    data_save.to_csv(path + r'\Data\info1\{}.csv'.format(name), header = True, 
                   index = None, sep = ';')
#%%
    
for col in list(data_final):
    if isinstance(data_final[col].values[0],list):
        print("'" + col + "',")
   # if isinstance(data_final[col][0],list):
   #     print(col)