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

## Model Performance Metrics

Metrics used to assess the model's performance is **Cosine Similarity** 

## References
Inspired from SemEval 2017 Task 5

Mengxiao Jiang, et al. 2017. Ecnu at semeval-2017 task 5: An ensemble of regression algorithms with effective features for fine-grained sentiment analysis in financial domain. In Proceedings of the 11th International Workshop on Semantic Evaluation (SemEval-2017). Association for Computational Linguistics, Vancouver, Canada. http://alt.qcri.org/semeval2017/.

Deepanway Ghosal, et al. 2017. Iitp at semeval-2017 task 5: An ensemble of deep learning and feature based models for financial sentiment analysis. In Proceedings of the 11th International Workshop on Semantic Evaluation (SemEval-2017). Association for Computational Linguistics, Vancouver, Canada. http://alt.qcri.org/semeval2017/.

