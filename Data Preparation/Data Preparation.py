
PATH_ROOT='C:/Users/Louis Owen/Desktop/NLP_Stacking_Ensemble/'

print('==================== Importing Packages ====================')

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import pandas as pd
import re
import json
import math
import string
import numpy as np
from bs4 import BeautifulSoup
import gensim

import contractions
import inflect
import string

import stanfordnlp
stanfordnlp.download('en') 
import nltk
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

from nltk import pos_tag
from nltk.corpus import wordnet as wn
from nltk.tokenize import wordpunct_tokenize,TweetTokenizer
from nltk import word_tokenize, pos_tag, ne_chunk
from nltk.stem.porter import *
from nltk.stem import WordNetLemmatizer
from scipy import sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from textblob import TextBlob
from sklearn.preprocessing import StandardScaler,MinMaxScaler

#------------------------------------------------------------------------------------------
print("==================== Importing Supporting Files ====================")

#Abbreviation & Slang Dict
abb_df = pd.read_table(PATH_ROOT+'Supporting_Files/'+'emnlp_dict.txt', sep='\s+', names=('Abbreviation', 'Normal'))
abb=pd.Series(abb_df['Normal'])
abb.index=abb_df['Abbreviation']
abb_dict=dict(abb)

#AFINN Sentiment Lexicon
AFINN_df = pd.read_table(PATH_ROOT+'Supporting_Files/'+'AFINN/'+'AFINN-111.txt', names=('Word', 'Sentiment'))
AFINN=pd.Series(AFINN_df['Sentiment'])
AFINN=((AFINN-AFINN.min())/(AFINN.max()-AFINN.min()))*(1-(-1))+(-1) #Rescaling in [-1,1]
AFINN.index=AFINN_df['Word']
AFINN_dict=dict(AFINN)

#Bing-Liu Sentiment Lexicon
pos = pd.read_table(PATH_ROOT+'Supporting_Files/'+'Bing-Liu-opinion-lexicon-English/'+'positive-words.txt',names='P')
neg=pd.read_table(PATH_ROOT+'Supporting_Files/'+'Bing-Liu-opinion-lexicon-English/'+'negative-words.txt',names='N',encoding='latin-1')
BingLiu_dict={'pos':pos['P'].tolist(),'neg':neg['N'].tolist()}

#General Enquirer Sentiment Lexicon
General_Inquirer_df=pd.read_csv(PATH_ROOT+'Supporting_Files/'+'General Inquirer Lexicon/'+'inquirerbasic.csv',index_col='Entry')
General_Inquirer_df=General_Inquirer_df[['Positiv','Negativ']]
General_Inquirer_dict={'pos':General_Inquirer_df[pd.isnull(General_Inquirer_df['Positiv'])==False]['Positiv'].index.tolist(),
                      'neg':General_Inquirer_df[pd.isnull(General_Inquirer_df['Negativ'])==False]['Positiv'].index.tolist()}

#NRC Hashtag Sentiment Lexicon
hs=pd.read_table(PATH_ROOT+'Supporting_Files/'+'NRC-Sentiment-Emotion-Lexicons/AutomaticallyGeneratedLexicons/NRC-Hashtag-Sentiment-Lexicon-v1.0/'+'HS-unigrams.txt',names=('Hashtag','PMI(w, pos) -PMI(w, neg)','n_pos','n_neg'),encoding='latin-1')
hs=hs[pd.isnull(hs.Hashtag)==False]
hs['PMI(w, pos) -PMI(w, neg)']=((hs['PMI(w, pos) -PMI(w, neg)']-hs['PMI(w, pos) -PMI(w, neg)'].min())/(hs['PMI(w, pos) -PMI(w, neg)'].max()-hs['PMI(w, pos) -PMI(w, neg)'].min()))*(1-(-1))+(-1) #Rescaling in [-1,1]
nrc=hs['PMI(w, pos) -PMI(w, neg)']
nrc.index=hs['Hashtag']
NRC_hashtag_dict=dict(nrc)

#Sentiwordnet Sentiment Lexicon
sentiwordnet=pd.read_table(PATH_ROOT+'Supporting_Files/'+'SentiWordNet/'+'SentiWordNet_3.0.0.txt',names=('POS','ID','PosScore','NegScore','SynsetTerms','Gloss'),encoding='latin-1')
sentiwordnet=sentiwordnet[pd.isnull(sentiwordnet.POS)==False]
sentiwordnet['score']=sentiwordnet['PosScore']-sentiwordnet['NegScore']

#------------------------------------------------------------------------------------------

print("==================== Importing Data ====================")

with open(PATH_ROOT+'Raw Data/'+'Microblog_Trainingdata-twitter_full.json') as train_file:
    dict_train = json.load(train_file)
microblog_train_twitter_full = pd.DataFrame.from_dict(dict_train)

with open(PATH_ROOT+'Raw Data/'+'Microblog_Trainingdata-stocktwits_full.json') as train_file:
    dict_train = json.load(train_file)
microblog_train_stocktwits_full = pd.DataFrame.from_dict(dict_train)


def rebuild_data(microblog_train_twitter_full,microblog_train_stocktwits_full):

	print("==================== Rebuilding Data ====================")

	twitter_df=microblog_train_twitter_full[['cashtag','sentiment score','spans','text','created_at']].copy()
	twitter_df['source']=['twitter' for x in range(len(twitter_df))] #add source column
	twitter_df['created_at']=pd.to_datetime(twitter_df['created_at']).apply(lambda x: '[0am,9am)' if (x.hour>=0 and x.hour<9) else '[9am,3pm)' if (x.hour>=9 and x.hour<15) else '[3pm,24pm)')  #encoding time created

	stocktwits_df=microblog_train_stocktwits_full[['cashtag','sentiment score','spans']].copy()
	stocktwits_message= microblog_train_stocktwits_full['message'].apply(pd.Series) #message data
	stocktwits_user=stocktwits_message['user'].apply(pd.Series) #user data

	stocktwits_df['text']=stocktwits_message['body']
	stocktwits_df['created_at']=stocktwits_message['created_at']
	stocktwits_df['source']=microblog_train_stocktwits_full['source']
	stocktwits_df['official_account']=stocktwits_user['official']
	stocktwits_df['sentiment']=stocktwits_message['entities'].apply(pd.Series)['sentiment'].apply(lambda x : x['basic'] if (type(x) is dict) else np.nan)
	stocktwits_df['liked_by_self']=stocktwits_message['liked_by_self']
	stocktwits_df['conversation_parent']=stocktwits_message['conversation'].apply(lambda x : x['parent'] if (type(x) is dict) else np.nan)
	stocktwits_df['conversation_replies']=stocktwits_message['conversation'].apply(lambda x : x['replies'] if (type(x) is dict and not math.isnan(x['replies'])) else 0)
	stocktwits_df['conversation_replies']=stocktwits_df['conversation_replies'].apply(lambda x: (x-min(stocktwits_df['conversation_replies']))/(max(stocktwits_df['conversation_replies'])-min(stocktwits_df['conversation_replies']))) #min-max scaling
	stocktwits_df['total_likes']=stocktwits_message['likes'].apply(lambda x : x['total'] if (type(x) is dict and not math.isnan(x['total'])) else 0)
	stocktwits_df['total_likes']=stocktwits_df['total_likes'].apply(lambda x: (x-min(stocktwits_df['total_likes']))/(max(stocktwits_df['total_likes'])-min(stocktwits_df['total_likes']))) #min-max scaling
	stocktwits_df['created_at']=pd.to_datetime(stocktwits_df['created_at']).apply(lambda x: '[0am,9am)' if (x.hour>=0 and x.hour<9) else '[9am,3pm)' if (x.hour>=9 and x.hour<15) else '[3pm,24pm)') #encoding time created
	#convert to numeric
	twitter_df['sentiment score']=pd.to_numeric(twitter_df['sentiment score'])
	stocktwits_df['sentiment score']=pd.to_numeric(stocktwits_df['sentiment score'])
	#One hot encoding
	stocktwits_df['official_account']=stocktwits_df['official_account'].apply(lambda x: 1 if x==True else 0 if x==False else x)
	stocktwits_df['liked_by_self']=stocktwits_df['liked_by_self'].apply(lambda x: 1 if x==True else 0 if x==False else x)
	stocktwits_df['conversation_parent']=stocktwits_df['conversation_parent'].apply(lambda x: 1 if x==True else 0 if x==False else x)

	#Concatenate both dataframe
	concat_df=pd.concat([stocktwits_df,twitter_df])
	concat_df=concat_df[pd.isnull(concat_df.text)==False]
	concat_df=concat_df.reset_index()

	return(concat_df)

def tokenize(sentence):
	'''
	tokenize input sentence into token
	'''
	token_list=nltk.regexp_tokenize(sentence, pattern=r"\s|[\.,;]\D", gaps=True)
	return(token_list)

def clean_data(concat_df):

	print("==================== Cleaning Data ====================")

	#Inspired by: 
	# https://www.dotnetperls.com/punctuation-python
	# https://github.com/tthustla/twitter_sentiment_analysis_part1/blob/master/Capstone_part2.ipynb
	# https://github.com/Deffro/text-preprocessing-techniques/blob/master/techniques.py

	#Word ordinal encoding
	p = inflect.engine()
	word_to_number_mapping = {}
	for i in range(1, 2000):
		word_form = p.number_to_words(i)  # 1 -> 'one'
		ordinal_word = p.ordinal(word_form)  # 'one' -> 'first'
		ordinal_number = p.ordinal(i)  # 1 -> '1st'
		word_to_number_mapping[ordinal_word] = ordinal_number  # 'first': '1st'
	  
	  
	def elongated_word(word):
		"""
	  	Replaces an elongated word with its basic form, unless the word exists in the lexicon 
	  	"""
		repeat_regexp = re.compile(r'(\w*)(\w)\2(\w*)')
		repl = r'\1\2\3'
		if (len(word)>2 and word[0] != '$'):#if not Stock Market symbol
			if wn.synsets(word):
				return word
			repl_word = repeat_regexp.sub(repl, word)
			if repl_word != word:      
				return elongated_word(repl_word)
			else:       
				return repl_word
		else:
			return word

	def isfloat(value):
		''' 
		Check if value is float or not
		'''
		try:
			float(value)
			return True
		except ValueError:
			return False

	def sentences_cleaner(sentence):
		'''
		clean input sentence  
		'''
		try:
			mention_pat= r'@[A-Za-z0-9_]+'
			mention_2_pat=r'@[A-Za-z0-9_]+:\s'
			retweet_pat=r'^RT +'
			dollars_pat=r'\$ +'
			http_pat = r'https?://[^ ]+'
			www_pat = r'www.[^ ]+'
			apos_pat=r'"+|"$|"+"$'

			soup = BeautifulSoup(sentence, 'lxml')
			souped = soup.get_text()

			#HTML decoding remove BOM
			try:
				bom_removed = souped.decode("utf-8-sig").replace(u"\ufffd", "?")
			except:
				bom_removed = souped
			
			#Delete mention
			stripped = re.sub(mention_2_pat,"", bom_removed)
			stripped = re.sub(mention_pat,"", stripped)
			
			#Delete retweet
			stripped=re.sub(retweet_pat,"",stripped)
			
			#Transform any url into '_url'
			stripped = re.sub(http_pat, '_url', stripped)
			stripped = re.sub(www_pat, '_url', stripped)

			#Transfrom abbreviation & slang word  into normal words based on abb_dict corpus
			abbreviation_handled=' '.join(pd.Series(stripped.split()).apply(lambda x: abb_dict[x] if x in abb_dict.keys() else x).to_list())

			#Transform contracted words into normal words
			contraction_handled =contractions.fix(abbreviation_handled)
			
			#Join the stock symbol
			dollars_handled=re.sub(dollars_pat,'$',contraction_handled)
			
			#Transform elongated words into normal words
			elongated_handled=' '.join(pd.Series(dollars_handled.split()).apply(lambda x: elongated_word(x[:-1])+x[-1] if (x[-1] in string.punctuation and not isfloat(x)) else elongated_word(x) if not isfloat(x) else x))
			
			#Transform ordinal number
			ordinal_handled=' '.join(pd.Series(elongated_handled.split()).apply(lambda x: word_to_number_mapping[x.lower()] if x.lower() in word_to_number_mapping.keys() else x))
			
			#Remove unnecesary apostrophes 
			apos_handled=re.sub(apos_pat,'',ordinal_handled)
			
			#Split Last Word Punctuation
			wordpunct=wordpunct_tokenize(apos_handled)
			if (len(wordpunct[-1])>1 and wordpunct[-1][-1] in string.punctuation and wordpunct[-2] not in string.punctuation) or (wordpunct[-1] in string.punctuation and wordpunct[-2] not in string.punctuation):
				words =tokenize(apos_handled)
				words[-1]=wordpunct[-2]
				words.append(wordpunct[-1])
			else:
				words =tokenize(apos_handled)

			return (" ".join(words)).strip()
		except:
			return sentence

	concat_df['clean_text']=concat_df['text'].apply(lambda x: sentences_cleaner(x))

	print('BEFORE CLEANING: {} \n'.format(concat_df.loc[81,'text']))

	print('AFTER CLEANING: {}'.format(sentences_cleaner(concat_df.loc[81,'text'])))

	return(concat_df)

#dictionary that contains pos tags and their explanations
# 'CC': 'coordinating conjunction','CD': 'cardinal digit','DT': 'determiner',
# 'EX': 'existential there (like: \"there is\" ... think of it like \"there exists\")',
# 'FW': 'foreign word','IN':  'preposition/subordinating conjunction','
# JJ': 'adjective \'big\'','JJR': 'adjective, comparative \'bigger\'',
# 'JJS': 'adjective, superlative \'biggest\'', 'LS': 'list marker 1)', 'MD': 'modal could, will',
# 'NN': 'noun, singular \'desk\'', 'NNS': 'noun plural \'desks\'',
#'NNP': 'proper noun, singular \'Harrison\'','NNPS': 'proper noun, plural \'Americans\'',
# 'PDT': 'predeterminer \'all the kids\'','POS': 'possessive ending parent\'s',
# 'PRP': 'personal pronoun I, he, she','PRP$': 'possessive pronoun my, his, hers',
# 'RB': 'adverb very, silently,', 'RBR': 'adverb, comparative better',
# 'RBS': 'adverb, superlative best','RP': 'particle give up', 'TO': 'to go \'to\' the store.',
# 'UH': 'interjection errrrrrrrm','VB': 'verb, base form take','VBD': 'verb, past tense took',
# 'VBG': 'verb, gerund/present participle taking','VBN': 'verb, past participle taken',
# 'VBP': 'verb, sing. present, non-3d take','VBZ': 'verb, 3rd person sing. present takes',
# 'WDT': 'wh-determiner which','WP': 'wh-pronoun who, what','WP$': 'possessive wh-pronoun whose',
# 'WRB': 'wh-abverb where, when','QF' : 'quantifier, bahut, thoda, kam (Hindi)',
# 'VM' : 'main verb','PSP' : 'postposition, common in indian langs','DEM' : 'demonstrative, common in indian langs'

#Extract Parts of Speech as BOW
def extract_pos(doc):
#pos_dict = {'CC':0, 'CD':0,'DT':0,'EX':0,'FW':0,'JJ':0,'JJR':0,'JJS':0,'LS':0,'MD':0,
#			'NN':0,'NNS':0,'NNP':0,'NNPS':0,'PDT':0,'POS':0,'PRP':0,'PRP$':0,'RB':0,
#			'RBR':0,'RBS':0,'RP':0,'TO':0,'UH':0,'VB':0,'VBD':0,'VBG':0,'VBN':0,'VBP':0,
#			'VBZ':0,'VM':0,'WDT':0,'WP':0,'WP$':0,'WRB':0,'QF':0,'PSP':0,'DEM':0}
	pos_dict = {'VB':0,'VBD':0,'VBG':0,'VBN':0,'VBP':0,'VBZ':0,'VM':0}
	try:
		for sent in doc.sentences:
			for wrd in sent.words:
				if wrd.pos in pos_dict.keys():
					pos_dict[wrd.pos]+=1
    	#return BOW of POS
		return pos_dict
	except:
		return pos_dict
  
  
def n_grams_handled(sentence):
	'''
	Filter before generate n-gram
	'''
	try:
		tk=TweetTokenizer()
		cashtag_pat=r'\$[^\s]+'
		hashtag_pat=r'#([^\s]+)'
		word_number_pat=r'\w*\d\w*'

		#Remove word which has length < 2
		stripped=' '.join([word for word in sentence.split() if len(word)>=2])

		#Remove hashtag
		hashtag_handled= re.sub(hashtag_pat,"", stripped)

		#Remove cashtag
		cashtag_handled= re.sub(cashtag_pat,"", hashtag_handled)

		#Remove word with number
		number_handled= re.sub(word_number_pat,"", cashtag_handled)

		#Remove unnecesary white spaces
		words = tk.tokenize(number_handled)
		words = [x for x in words if x not in string.punctuation]
		clean_sentence=(" ".join(words)).strip()
		return  clean_sentence
	except:
		return sentence

def countAllCaps(text):
	""" Input: a text, Output: how many words are all caps """
	return len(re.findall("[A-Z]{2,}", text))

def countHashtag(text):
	""" Input: a text, Output: how many hastags in front of a word """
	return len(re.findall(r'#([^\s]+)', text))

def is_ordinal_numbers(sentences):
	occur=0
	for word in tokenize(sentences):
		if ((word[-2:] in ['st','nd','rd','th']) and (isfloat(word[:-2]))):
			occur=1
	return(occur)

def countMultiExclamationMarks(sentences):
	""" Replaces repetitions of exlamation marks """
	return len(re.findall(r"(\!)\1+", sentences))
  
def countMultiQuestionMarks(sentences):
	""" Count repetitions of question marks """
	return len(re.findall(r"(\?)\1+", sentences))
  
def sentence_synset(sentence):
	'''
	return the wordnet synset of each word in the sentence
	''' 
	def penn_to_wn(tag):
		if tag.startswith('J'):
			return wn.ADJ
		elif tag.startswith('N'):
			return wn.NOUN
		elif tag.startswith('R'):
			return wn.ADV
		elif tag.startswith('V'):
			return wn.VERB
		return None

	tagged = pos_tag(tokenize(sentence))

	synsets_list = []
	lemmatzr = WordNetLemmatizer()

	for token in tagged:
		wn_tag = penn_to_wn(token[1])
		if not wn_tag:
	  		continue

		lemma = lemmatzr.lemmatize(token[0], pos=wn_tag)
		try:
			synsets_list.append(wn.synsets(lemma, pos=wn_tag)[0])
		except:
			None
	return synsets_list

def min_multiple_list(S):
	'''
	Minimum pooling
	'''
	it=range(len(S)-1)
	minim=S[0]
	for i in it:
		minim=np.minimum(minim,S[i])
	return(minim)

def max_multiple_list(S):
	'''
	Maximum pooling
	'''
	it=range(len(S)-1)
	maxim=S[0]
	for i in it:
		maxim=np.maximum(maxim,S[i])
	return(maxim)

def rescaling(df,columns,scale_type='Standard'):
	'''
	Function for Feature Scaling
	'''
	scale_type=scale_type.lower()
	scaled_X=df.drop(columns,1)
	X=df[columns]

	if scale_type=='minmax':
		scaler=MinMaxScaler(feature_range=(0,1))
	elif scale_type=='standard':
		scaler=StandardScaler()

	scaled_column=scaler.fit_transform(X)
	scaled_column=pd.DataFrame(scaled_column,columns=columns)
	for column in columns:
		scaled_X[column]=scaled_column[column].tolist()

	return(scaled_X)

def feature_engineering_split(df):

	print("==================== Feature Engineering by Splitting ====================")
	#List of POS-Tag
	#pos_key = ['CC', 'CD','DT','EX','FW','JJ','JJR','JJS','LS','MD', 'NN','NNS','NNP','NNPS','PDT'
	#	 	    ,'POS','PRP','PRP$','RB', 'RBR','RBS','RP','TO','UH','VB','VBD','VBG','VBN','VBP',
	#			'VBZ','VM','WDT','WP','WP$','WRB','QF','PSP','DEM']
	pos_key = ['VB','VBD','VBG','VBN','VBP','VBZ','VM']

	#Initiate pipeline for POS-Tagging
	nlp = stanfordnlp.Pipeline(processors = "tokenize,pos")

	#Inititate class for Lemmatization
	lemmatizer = WordNetLemmatizer()

	#Initiate class for Stemming
	stemmer = PorterStemmer()

	#Lemmatization+Stemming
	df['base_text']=df['clean_text'].apply(lambda x: ' '.join(pd.Series(tokenize(x)).apply(lambda wrd: stemmer.stem(lemmatizer.lemmatize(wrd)) if wrd[0]!='$' else wrd).to_list()) if type(x)==str else np.nan)
	print('Done Base Text')

	#Create POS-Tag features
	for tag in pos_key:
		df['POS_'+tag]=df['clean_text'].apply(lambda x: extract_pos(nlp(x))[tag] if type(x)==str else np.nan)
	print('Done POS Tag')

	#Binary Feature '+num'
	df["'+num"]=df['clean_text'].apply(lambda x: 1 if ((type(x)==str) and len(re.findall(r'\+\d+\s|\+\d+[!,.;:?/]|\+\d+$',x))>0) else 0  if type(x)==str else np.nan)

	#Binary Feature '-num'
	df["'-num"]=df['clean_text'].apply(lambda x: 1 if ((type(x)==str) and len(re.findall(r'\-\d+\s|\-\d+[!,.;:?/]|\-\d+$',x))>0) else 0  if type(x)==str else np.nan)

	#Binary Feature 'num%'
	df["num%"]=df['clean_text'].apply(lambda x: 1 if ((type(x)==str) and len(re.findall(r' \d.\d*%+|^\d.\d*%+|[!,.;:?/]\d.\d*%+| \d*%+|^\d*%+|[!,.;:?/]\d*%+',x))>0) else 0  if type(x)==str else np.nan)

	#Binary Feature '+num%'
	df["'+num%"]=df['clean_text'].apply(lambda x: 1 if ((type(x)==str) and len(re.findall(r'\+\d.\d*%+|\+\d*%+',x))>0) else 0  if type(x)==str else np.nan)

	#Binary Feature '-num%'
	df["'-num%'"]=df['clean_text'].apply(lambda x: 1 if ((type(x)==str) and len(re.findall(r'\-\d.\d*%+|\-\d*%+',x))>0) else 0  if type(x)==str else np.nan)

	#Binary Features '$num'
	df['$num']=df['clean_text'].apply(lambda x: 1 if ((type(x)==str) and len(re.findall(r'\$\d*%+',x))>0) else 0  if type(x)==str else np.nan)

	#Binary Feature mixed number and word
	df['word_num']=df['clean_text'].apply(lambda x: 1 if (type(x)==str and len(re.findall(r'\w*\d\w*',x))>0) else 0 if (type(x)==str) else np.nan)

	#Binary Feature ordinal number
	df['ordinal_num']=df['clean_text'].apply(lambda x: is_ordinal_numbers(x) if type(x)==str else np.nan)

	#Binary Feature  'num-num'
	df['num-num']=df['clean_text'].apply(lambda x: 1 if ((type(x)==str) and len(re.findall(r'\d*-\d+',x))>0) else 0  if type(x)==str else np.nan)

	#Binary Feature  'num-num%'
	df['num-num%']=df['clean_text'].apply(lambda x: 1 if ((type(x)==str) and len(re.findall(r'\d*-\d%+',x))>0) else 0  if type(x)==str else np.nan)

	#Binary Feature  'num-num-num'
	df['num-num-num']=df['clean_text'].apply(lambda x: 1 if ((type(x)==str) and len(re.findall(r'\d*-\d-\d+',x))>0) else 0  if type(x)==str else np.nan)

	#Binary Feature  'num/num'
	df['num/num']=df['clean_text'].apply(lambda x: 1 if ((type(x)==str) and len(re.findall(r'\d*/\d+',x))>0) else 0  if type(x)==str else np.nan)

	#Binary Feature  'num/num/num'
	df['num/num/num']=df['clean_text'].apply(lambda x: 1 if ((type(x)==str) and len(re.findall(r'\d*/\d/\d+',x))>0) else 0  if type(x)==str else np.nan)

	#Binary Feature  only numbers(no symbol and characters)
	df['only_number']=df['clean_text'].apply(lambda x:1 if (type(x)==str and any(isfloat(wrd) for wrd in tokenize(x))) else 0 if type(x)==str else np.nan)
	print('Done Keyword+num')

	f_plus=lambda x: pd.Series(tokenize(x)).apply(lambda wrd: 1 if len(re.findall(r'\+\d.\d*%+|\+\d*%+',wrd))>0 else 0)
	g_plus=lambda y: f_plus(y)[f_plus(y)==1].index.tolist()
	f_min=lambda x: pd.Series(tokenize(x)).apply(lambda wrd: 1 if len(re.findall(r'\-\d.\d*%+|\-\d*%+',wrd))>0 else 0)
	g_min=lambda y: f_min(y)[f_min(y)==1].index.tolist()

	#Binary Feature  'call'(or 'calls' or 'called') before '+num%'
	df['call_+num%']=df['clean_text'].apply(lambda z: 1 if (type(z)==str and any((tokenize(z)[i-1]=='call' or tokenize(z)[i-1]=='calls' or tokenize(z)[i-1]=='called') for i in g_plus(z))) else 0 if type(z)==str else np.nan)

	#Binary Feature  'call'(or 'calls' or 'called') before '-num%'
	df['call_-num%']=df['clean_text'].apply(lambda z: 1 if (type(z)==str and any((tokenize(z)[i-1]=='call' or tokenize(z)[i-1]=='calls' or tokenize(z)[i-1]=='called') for i in g_min(z))) else 0 if type(z)==str else np.nan)

	#Binary Feature  'put'(or 'puts') before '+num%'  
	df['put_+num%']=df['clean_text'].apply(lambda z: 1 if (type(z)==str and any((tokenize(z)[i-1]=='put' or tokenize(z)[i-1]=='puts') for i in g_plus(z))) else 0 if type(z)==str else np.nan)

	#Binary Feature  'put'(or 'puts') before '-num%'
	df['put_-num%']=df['clean_text'].apply(lambda z: 1 if (type(z)==str and any((tokenize(z)[i-1]=='put' or tokenize(z)[i-1]=='puts') for i in g_min(z))) else 0 if type(z)==str else np.nan)
	              
	#Binary Feature 'Bull' or 'Bullish'
	df['bull']=df['clean_text'].apply(lambda x: 1 if (type(x)==str and ('bull' or 'bullish') in x.split()) else 0 if type(x)==str else np.nan)
	               
	#Binary Feature 'Bear' or 'Bearish'
	df['bear']=df['clean_text'].apply(lambda x: 1 if (type(x)==str and ('bear' or 'bearish') in x.split()) else 0 if type(x)==str else np.nan)                
	print('Done Specific Keyword')

	tk=TweetTokenizer()
	#Calculate the number of '!'
	df['number_of_!']=df['clean_text'].apply(lambda x: tk.tokenize(x).count('!') if type(x)==str else np.nan)

	#Calculate the number of '?'
	df['number_of_?']=df['clean_text'].apply(lambda x: tk.tokenize(x).count('?') if type(x)==str else np.nan)

	#Calculate the number of '$'
	df['number_of_$']=df['clean_text'].apply(lambda x: tk.tokenize(x).count('$') if type(x)==str else np.nan)

	#Calculate the number of continuous '!'
	df['continous_!']=df['clean_text'].apply(lambda x: countMultiExclamationMarks(x) if type(x)==str else np.nan)

	#Calculate the number of continuous '?'
	df['continous_?']=df['clean_text'].apply(lambda x: countMultiQuestionMarks(x) if type(x)==str else np.nan)
	print('Done Punctation Count')

	#Calculate the number of Caps word
	df['caps_word']=df['clean_text'].apply(lambda x: countAllCaps(' '.join([i for i in x.split() if i[0]!='$'])) if type(x)==str else np.nan)
	print('Done Caps words')

	#Calculate the number of Hashtags
	df['hashtags']=df['clean_text'].apply(lambda x: countHashtag(x) if type(x)==str else np.nan)
	print('Done Hashtags')
	               
	#AFINN Sentiment Lexicon
	affin_sent_score=lambda x: pd.Series(tokenize(x)).apply(lambda wrd: AFINN_dict[wrd.lower()] if wrd.lower() in AFINN_dict.keys() else 0)
	affin_sent_binary=lambda x: pd.Series(tokenize(x)).apply(lambda wrd: 1 if (wrd.lower() in AFINN_dict.keys() and AFINN_dict[wrd.lower()]>0) else
	                                                     -1 if (wrd.lower() in AFINN_dict.keys() and AFINN_dict[wrd.lower()]<0) else 0)       
	#Sum Score
	df['AFINN_sum_score']=df['clean_text'].apply(lambda x: affin_sent_score(x).sum() if type(x)==str else np.nan)
	#Max Score
	df['AFINN_max_score']=df['clean_text'].apply(lambda x: affin_sent_score(x).max() if type(x)==str else np.nan)        
	#Min Score
	df['AFINN_min_score']=df['clean_text'].apply(lambda x: affin_sent_score(x).min() if type(x)==str else np.nan)  
	#Ratio of Positive Words
	df['AFINN_pos_ratio']=df['clean_text'].apply(lambda x: sum(1 for i in affin_sent_binary(x) if i==1)/len(tokenize(x)) if type(x)==str else np.nan)
	#Ratio of Negatiive Words
	df['AFINN_neg_ratio']=df['clean_text'].apply(lambda x: sum(1 for i in affin_sent_binary(x) if i==-1)/len(tokenize(x)) if type(x)==str else np.nan)  
	print('Done AFIIN Lexicon')

	#BingLiu Sentiment Lexicon
	bingliu_sent_binary=lambda x: pd.Series(tokenize(x)).apply(lambda wrd: 1 if wrd.lower() in BingLiu_dict['pos'] else -1 if wrd.lower() in BingLiu_dict['neg'] else 0)
	#Ratio of Positive Words
	df['BingLiu_pos_ratio']=df['clean_text'].apply(lambda x: sum(1 for i in bingliu_sent_binary(x) if i==1)/len(tokenize(x)) if type(x)==str else np.nan)
	#Ratio of Negative Words
	df['BingLiu_neg_ratio']=df['clean_text'].apply(lambda x: sum(1 for i in bingliu_sent_binary(x) if i==-1)/len(tokenize(x)) if type(x)==str else np.nan)
	print('Done BingLiu Lexicon')

	#General Inquirer Sentiment Lexicon
	general_inquirer_binary=lambda x: pd.Series(tokenize(x)).apply(lambda wrd: 1 if wrd.lower() in General_Inquirer_dict['pos'] else -1 if wrd.lower() in General_Inquirer_dict['neg'] else 0)
	#Ratio of Positive Words
	df['General_Inquirer_pos_ratio']=df['clean_text'].apply(lambda x: sum(1 for i in general_inquirer_binary(x) if i==1)/len(tokenize(x)) if type(x)==str else np.nan)
	#Ratio of Negative Words
	df['General_Inquirer_neg_ratio']=df['clean_text'].apply(lambda x: sum(1 for i in general_inquirer_binary(x) if i==-1)/len(tokenize(x)) if type(x)==str else np.nan)
	print('Done General Inquirer Lexicon')

	#NRC Hashtag Sentiment Lexicon
	nrc_hashtag_sent_score=lambda x: pd.Series(tokenize(x)).apply(lambda wrd: NRC_hashtag_dict[wrd.lower()] if wrd.lower() in NRC_hashtag_dict.keys() else 0)
	nrc_hashtag_sent_binary=lambda x: pd.Series(tokenize(x)).apply(lambda wrd: 1 if (wrd.lower() in NRC_hashtag_dict.keys() and NRC_hashtag_dict[wrd.lower()]>0) else
	                                                     -1 if (wrd.lower() in NRC_hashtag_dict.keys() and NRC_hashtag_dict[wrd.lower()]<0) else 0)       
	#Sum Score
	df['NRC_Hashtag_sum_score']=df['clean_text'].apply(lambda x: nrc_hashtag_sent_score(x).sum() if type(x)==str else np.nan)
	#Max Score
	df['NRC_Hashtag_max_score']=df['clean_text'].apply(lambda x: nrc_hashtag_sent_score(x).max() if type(x)==str else np.nan)        
	#Min Score
	df['NRC_Hashtag_min_score']=df['clean_text'].apply(lambda x: nrc_hashtag_sent_score(x).min() if type(x)==str else np.nan)  
	#Ratio of Positive Words
	df['NRC_Hashtag_pos_ratio']=df['clean_text'].apply(lambda x: sum(1 for i in nrc_hashtag_sent_binary(x) if i==1)/len(tokenize(x)) if type(x)==str else np.nan)
	#Ratio of Negatiive Words
	df['NRC_Hashtag_neg_ratio']=df['clean_text'].apply(lambda x: sum(1 for i in nrc_hashtag_sent_binary(x) if i==-1)/len(tokenize(x)) if type(x)==str else np.nan)  
	print('Done NRC Hashtag Sentiment Lexicon')

	#SentiWordNet Sentiment Lexicon
	sentiwordnet_list=sentiwordnet.ID.tolist()
	sent_to_synset=lambda x: pd.Series(sentence_synset(x))
	synset_to_offset=lambda x: int(str(x.offset()).zfill(8))
	get_value=lambda x: sentiwordnet[sentiwordnet.ID==synset_to_offset(x)]['score'].values[0]
	score_offset_check=lambda x: get_value(x) if (synset_to_offset(x) in sentiwordnet_list) else 0
	binary_offset_check=lambda x: 1 if (synset_to_offset(x) in sentiwordnet_list and get_value(x)>0) else  -1 if  (synset_to_offset(x) in sentiwordnet_list and get_value(x)<0) else 0
	sentiwordnet_score=lambda sent: sent_to_synset(sent).apply(lambda z: score_offset_check(z)) 
	sentiwordnet_binary=lambda sent: sent_to_synset(sent).apply(lambda z: binary_offset_check(z))
	#Sum Score
	df['SentiWordNet_sum_score']=df['clean_text'].apply(lambda x: sentiwordnet_score(x).sum() if type(x)==str else np.nan)
	#Max Score
	df['SentiWordNet_max_score']=df['clean_text'].apply(lambda x: sentiwordnet_score(x).max() if type(x)==str else np.nan)        
	#Min Score
	df['SentiWordNet_min_score']=df['clean_text'].apply(lambda x: sentiwordnet_score(x).min() if type(x)==str else np.nan)  
	#Ratio of Positive Words
	df['SentiWordNet_pos_ratio']=df['clean_text'].apply(lambda x: sum(1 for i in sentiwordnet_binary(x) if i==1)/len(sent_to_synset(x)) if (type(x)==str and len(sent_to_synset(x))>0) else 0 if type(x)==str else np.nan)
	#Ratio of Negatiive Words
	df['SentiWordNet_neg_ratio']=df['clean_text'].apply(lambda x: sum(1 for i in sentiwordnet_binary(x) if i==-1)/len(sent_to_synset(x)) if (type(x)==str and len(sent_to_synset(x))>0) else 0 if type(x)==str else  np.nan)  
	print('Done SentiWordNet Lexicon')
	return(df)

def feature_engineering(df):

	print("==================== Feature Engineering ====================")
	#n-grams
	for grams in [1,2,3,4]:
		nan_checker=lambda x: x if type(x)==str else ''
		  
		#Initiate class for BOW 
		bow_vectorizer= CountVectorizer(ngram_range=(grams,grams))
		#Initiate class for TF-IDF
		tfidf_vectorizer = TfidfVectorizer(norm=None, ngram_range=(grams,grams))

		#Create docs
		docs=df['clean_text'].apply(lambda x: n_grams_handled(x))

		#Create TF-IDF matrix
		tfidf_matrix = tfidf_vectorizer.fit_transform(docs.apply(lambda x: nan_checker(x)).to_list())

		#Create TF-IDF n-grams
		df['Avg_TFIDF_'+str(grams)+'-grams']=[np.mean([x for x in tfidf_matrix[i].toarray()[0].tolist() if x!=0]) for i in range(len(df))]

	print('Done n-grams')

	return(df)

def PMI_dict_maker(df): 
	'''
	Function to create a PMI dictionary which will be used in prediction phase
	'''
	BOW_df= pd.DataFrame(columns=['pos','neutral','neg'])
	words_set = set()

	#Creating the dictionary of words
	it=range(len(df))
	for i in it:
		score=df.loc[i,'sentiment score']
		if score>0:
			score='pos'
		elif score<0:
			score='neg'
		else:
			score='neutral'
		try:
			text=df.loc[i,'clean_text']
			cleaned_text=n_grams_handled(text)
			splitted_text=tokenize(cleaned_text)
			for word in splitted_text:
				if word not in words_set:#check if this word already counted or not in the full corpus
					words_set.add(word)
					BOW_df.loc[word] = [0,0,0]
					BOW_df.loc[word,score]+=1
				else:
					BOW_df.loc[word,score]+=1
		except:
			None
	return(BOW_df)  

def rf_ngram_dict_maker(df,gram): 
	'''
	Function to create a RF n-gram dictionary which will be used in prediction phase
	'''
	BOW_df= pd.DataFrame(columns=['pos','neutral','neg'])
	words_set = set()

	#Creating the rf_ngram dictionary of words
	it=range(len(df))
	for i in it:
		score=df.loc[i,'sentiment score']
		if score>0:
			score='pos'
		elif score<0:
			score='neg'
		else:
			score='neutral'
		try:
			text=df.loc[i,'clean_text']
			cleaned_text=n_grams_handled(text)
			splitted_text=tokenize(cleaned_text)
			if gram==1:
				for word in splitted_text:
					if word not in words_set:#check if this word already counted or not in the full corpus
						words_set.add(word)
						BOW_df.loc[word] = [0,0,0]
						BOW_df.loc[word,score]+=1
					else:
						BOW_df.loc[word,score]+=1
			elif gram==2:
				it_2_gram=range(len(splitted_text)-1)
				bigram=lambda x: splitted_text[x]+' '+splitted_text[x+1]
				for i in it_2_gram:
					if bigram(i) not in words_set:
						words_set.add(bigram(i))
						BOW_df.loc[bigram(i)] = [0,0,0]
						BOW_df.loc[bigram(i),score]+=1
					else:
						BOW_df.loc[bigram(i),score]+=1
			elif gram==3:
				it_3_gram=range(len(splitted_text)-2)
				trigram=lambda x: splitted_text[x]+' '+splitted_text[x+1]+' '+splitted_text[x+2]
				for i in it_3_gram:
					if trigram(i) not in words_set:
						words_set.add(trigram(i))
						BOW_df.loc[trigram(i)] = [0,0,0]
						BOW_df.loc[trigram(i),score]+=1
					else:
						BOW_df.loc[trigram(i),score]+=1
			elif gram==4:
				it_4_gram=range(len(splitted_text)-3)
				fourgram=lambda x: splitted_text[x]+' '+splitted_text[x+1]+' '+splitted_text[x+2]+' '+splitted_text[x+3]
				for i in it_4_gram:
					if fourgram(i) not in words_set:
						words_set.add(fourgram(i))
						BOW_df.loc[fourgram(i)] = [0,0,0]
						BOW_df.loc[fourgram(i),score]+=1
					else:
						BOW_df.loc[fourgram(i),score]+=1 
		except:
			None
	return(BOW_df)


def parallelize_dataframe(df, func, n_split):
	'''
	Function to parallelize a dataframe
	'''
	df_split = np.array_split(df, n_split)
	df_pool=func(df_split[0])
	for i in range(n_split-1):
		x=df_split[i+1]
		x=func(x.copy())
		df_pool = pd.concat([df_pool,x],ignore_index=True)
	return df_pool

def main():
	concat_df=rebuild_data(microblog_train_twitter_full,microblog_train_stocktwits_full)

	clean_df=clean_data(concat_df)

	draft_engineered_df=parallelize_dataframe(clean_df, feature_engineering_split,n_split=4)

	engineered_df=feature_engineering(draft_engineered_df)

	engineered_df.to_csv(PATH_ROOT+'df_prepared.csv')

	rf_1_gram_df=rf_ngram_dict_maker(clean_df,gram=1)
	rf_1_gram_df.to_csv(PATH_ROOT+'rf_1_gram_df.csv')
	
	rf_2_gram_df=rf_ngram_dict_maker(clean_df,gram=2)
	rf_2_gram_df.to_csv(PATH_ROOT+'rf_2_gram_df.csv')
	
	rf_3_gram_df=rf_ngram_dict_maker(clean_df,gram=3)
	rf_3_gram_df.to_csv(PATH_ROOT+'rf_3_gram_df.csv')
	
	rf_4_gram_df=rf_ngram_dict_maker(clean_df,gram=4)
	rf_4_gram_df.to_csv(PATH_ROOT+'rf_4_gram_df.csv')
	
	PMI_df=PMI_dict_maker(clean_df)
	PMI_df.to_csv(PATH_ROOT+'PMI_df.csv')

if __name__ == '__main__':
	main()