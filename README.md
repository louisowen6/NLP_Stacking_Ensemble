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

## Model Performance Metrics

The metrics used to assess the model's performance is **Cosine Similarity** 

## Model

There are 4 models created and 1 ensemble model to combine those 4 models.
 - Multi Layer Perceptron Feature Driven
 - Multi Layer Perceptron Simple Word Embedding
 - Convolutional Neural Network
 - Long Short-Term Memory Neural Network
 - Multi Layer Perceptron Stacking Ensemble

### MLP Feauture Driven

This model aims to get the 


## References
Inspired from SemEval 2017 Task 5

Mengxiao Jiang, et al. 2017. Ecnu at semeval-2017 task 5: An ensemble of regression algorithms with effective features for fine-grained sentiment analysis in financial domain. In Proceedings of the 11th International Workshop on Semantic Evaluation (SemEval-2017). Association for Computational Linguistics, Vancouver, Canada. http://alt.qcri.org/semeval2017/.

Deepanway Ghosal, et al. 2017. Iitp at semeval-2017 task 5: An ensemble of deep learning and feature based models for financial sentiment analysis. In Proceedings of the 11th International Workshop on Semantic Evaluation (SemEval-2017). Association for Computational Linguistics, Vancouver, Canada. http://alt.qcri.org/semeval2017/.

