# Sentiment Analysis in Stock Market using CNN, LSTM, MLP, NLP and Stacking Ensemble

## Background

### Why?

Behavior of stock market prices not only influenced by the historical prices but also influenced by the news or opinions from the market it self. 

### How?

Given the news or opinions data which annotated with sentiment score from financial experts (scaled from -1 to 1), one should predict the sentiment score of the newly unseen data.

### What?

Using Neural Network and Natural Language Processing (NLP) to preprocess and train the given data in order to predict the newly unseen data

## Dataset

### Stocktwits Messages

Consists of microblog messages focusing on stock market events and assessments from investors and traders, exchanged via the Stock-Twits microblogging platform 

### Twitter Messages

Some stock market discussion also takes place on the Twitter platform. In order to extend and diversify our data sources, we extract Twitter posts containing company stock symbols (cashtags) 

### Data Scraping

Data is collected via scraping through official website API. The syntax of scraping is provided by [SemEval](http://alt.qcri.org/semeval2017/task5/)

You can see the .json scraped data for [Stocktwits](Raw%20Data/Microblog_Trainingdata-stocktwits_full.json) and for [Twitter](Raw%20Data/Microblog_Trainingdata-twitter_full.json)

## Data Preparation

The data provided from the official website are not clean yet and we have to do some feature engineering and feauture selection before jump into the modeling process. 

### Data Cleaning & Feature Engineering 

The Stocktwits and Twitter data are combined into one dataframe before doing data cleaning process. 

The tweets cleaning procedure including:
  - Remove HTML encoding: '&amp', '$quot', etc
  - Remove mention tag: '@userid1'
  - Remove Retweet symbol: 'RT'
  - Convert all URL into '_url'
  - Convert abbreviation and slang words into its basic form using [dictionary](https://github.com/louisowen6/NLP_Stacking_Ensemble/blob/master/Supporting_Files/emnlp_dict.txt)
  - Convert elongated word into its basic form: 'Winnn'
  - Convert ordinal words into ordinal number: 'first' is converted to '1st'

After done with the tweets cleaning, there are in total 86 variables created from the cleaned tweets text and from tweets metadata.

You can find the Notebook [here](https://github.com/louisowen6/NLP_Stacking_Ensemble/blob/master/Feature_Engineering_and_Data_Cleaning.ipynb) and [here](https://github.com/louisowen6/NLP_Stacking_Ensemble/blob/master/NER_Prep.ipynb)

### Feature Selection

After doing feature engineering, we have to do some analysis to select which features will be used in the modeling process. The analysis are as follows:
  - Missing Value Analysis
  - Constant Variables Analysis
  - Duplicated Variables Analysis
  - Correlated Variables Analysis
 
So, from 86 variables created in the feature engineering process we succeed to remove 14 variables.

You can find the Notebook [here](https://github.com/louisowen6/NLP_Stacking_Ensemble/blob/master/Feature_Selection.ipynb)

Now, we have 72 variables extracted from texts which will be used in the modeling process.

## Model Performance Metrics

The metrics used to assess the model's performance is **Cosine Similarity** 

## Model

There are 4 models created and 1 ensemble model to combine those 4 models.
 - Multi Layer Perceptron Feature Driven
 - Multi Layer Perceptron Simple Word Embedding
 - Convolutional Neural Network
 - Long Short-Term Memory Neural Network
 - Multi Layer Perceptron Stacking Ensemble

### MLP Feature Driven

This model aims to get the information from the 72 manually curated variables. The MLP has 3 hidden layers with tanh activation function both in the hidden layer and output layer. Number of nodes in the first, second, and third layer is 50, 30, 15. Dropout is also used in this model.

### MLP Simple Word Embedding

This model aims to get the information straights from the vector representation of texts. The MLP has 3 hidden layers with tanh activation function in the output layer and ReLu in the hidden layer. Number of nodes in the first, second, and third layer is 50, 25, 10. Dropout is also used in this model.

### Convolutional Neural Network

CNN aims to get the local behaviour within the texts by sliding over 1,2,3,4 words at each time. Gaussian Noise with 0.01 variance is used to give noise into the input data. There are 25 filters for each window slide, so in total there are 100 filters with 1 dimension vector output for each filter. Max-pooling is used in each the output of each filter, resulting 100 scalar in total. Then all of the scalar are concatenated into one 100-dimensional vector. 

The output of this CNN is then integrated with MLP with 2 hidden layers with tanh activation function both in the hidden layer and output layer. Number of nodes in the first and second layer is 10 and 5. Dropout is also used in this MLP.

### Long Short-Term Memory



## Supporting Files

Here are the link to download supporting files used in this project which are not uploaded into the repository due to the large size
  - [AFINN Lexicon](http://corpustext.com/reference/sentiment_afinn.html)
  - [BingLiu Lexicon](https://www.cs.uic.edu/~liub/FBS/sentiment-analysis.html)
  - [General Inquirer Lexicon](http://www.wjh.harvard.edu/~inquirer/homecat.htm)
  - [NRC Hashtag Sentiment Lexicon](http://sentiment.nrc.ca/lexicons-for-research/)
  - [Senti WordNet](https://github.com/aesuli/sentiwordnet)
  - [Google Word2Vec Pre-Trained Model](https://drive.google.com/open?id=16A169DxZ-h9qU0i6rXCoSh_djkBWnd9V)
  - [GloVe Twitter Pre-Trained Model](https://drive.google.com/open?id=1p1IN9O_fpSQzPTFB5Y8CCOMXPIPU1WGV)

## References
Inspired from SemEval 2017 Task 5

Mengxiao Jiang, et al. 2017. Ecnu at semeval-2017 task 5: An ensemble of regression algorithms with effective features for fine-grained sentiment analysis in financial domain. In Proceedings of the 11th International Workshop on Semantic Evaluation (SemEval-2017). Association for Computational Linguistics, Vancouver, Canada. http://alt.qcri.org/semeval2017/.

Deepanway Ghosal, et al. 2017. Iitp at semeval-2017 task 5: An ensemble of deep learning and feature based models for financial sentiment analysis. In Proceedings of the 11th International Workshop on Semantic Evaluation (SemEval-2017). Association for Computational Linguistics, Vancouver, Canada. http://alt.qcri.org/semeval2017/.

