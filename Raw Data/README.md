# SemEval 2017 Task 5 - Subtask 1 "Fine-Grained Sentiment Analysis on Financial Microblogs"

This repository contains the data and source code for subtask 1 "Microblogs" of task 5 in SemEval 2017, "Fine-Grained Sentiment Analysis on Financial Microblogs and News" (see [task website](http://alt.qcri.org/semeval2017/task5/)).
It consists of a collection of financially relevant microblog messages from [Twitter](https://twitter.com/) and [Stocktwits](http://stocktwits.com/) which have been annotated for fine-grained sentiment. Since the terms of use of these platforms do not allow the redistribution of the message text, we include a script to help you download the data via the respective APIs.

## Preparation

You will need to prepare a few basic things:

1. Clone this repository `git clone https://bitbucket.org/ssix-project/semeval-2017-task-5-subtask-1.git semeval-2017-task-5-subtask-1`
2. Move into the cloned repository: `cd semeval-2017-task-5-subtask-1/`
3. You need to have both a `python` interpreter and `pip` installed
4. Install required dependecies: `pip install -r requirements.txt --upgrade`
5. [Create a new Twitter App](https://apps.twitter.com/app/new), then create a
   read-only Access Token, and fill in the missing details at `config.yml`
6. Create a StockTwits account, an application (https://stocktwits.com/developers/apps/new) and an API token (http://stocktwits.com/developers/docs/authentication), and also fill this in to `config.yml`


## Rebuild full sample

The [published sample](https://bitbucket.org/ssix-project/semeval-2017-task-5-subtask-1/src/75f7bd9f2e7ebf9e5e211b301447c55e90512c2e/Microblog_Trialdata.json?fileviewer=file-view-default)
is anonymised to not distribute any personal details.

To rebuild the full dataset, you need to execute the following script:

    python rebuild.py Microblog_Trialdata.json

This process will take time, depending on the pause configured at `config.yml`
to obey the [Twitter API rate limits](https://dev.twitter.com/rest/public/rate-limiting) and the [Stocktwits API rate limits](http://stocktwits.com/developers/docs/rate_limiting).

At the end it will create a `Task5_Microblog_Trialdata-full.json` with the full dataset rebuilt,
including both the original tweet data and annotations.

Please be aware that deleted tweets are not displayed in the final dataset and deleted twits are market with an "errors" field. 


## Annotations

Each message in Task5_Microblog_Trialdata-full.json is annotated with the following information:
1. `source`: platform where the message was posted, either `Twitter` or `Stocktwits`
2. `id`: unique Twitter or StockTwits ID of the message
3. `cashtag`: identifies the stock ticker symbol that the `sentiment` and `span` relate to
4. `sentiment`: a floating point value between `-1` (very bearish/negative) and `1` (very bullish/positive) denoting the sentiment expressed towards `cashtag`. `0` denotes neutral sentiment.
5. `spans`: a list of strings from the message which express sentiment

## Licenses

### Software

The software is available under the business-friendly license
[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).
Therefore, you are completely free to use the software for any purpose,
to distribute it, to modify it, and to distribute modified versions of the software,
including closed-source, under the terms of the license, without concern for royalties.

### Dataset

All of the data from Twitter are covered by [Twitter's Terms of Service](https://dev.twitter.com/terms/api-terms), while the Stocktwits data are covered by the [Stocktwits API Terms](http://stocktwits.com/developers/api-terms).

The annotations are licensed under the [Creative Commons Attribution-Non-Commercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/) license.
Please cite the SemEval 2017 task description paper for task 5 (once available) when using this dataset.

If you are interested in commercial use of these data, please [contact the SSIX consortium|http://ssix-project.eu/contact-us/].

## Acknowledgements

These resources were created in the context of the [SSIX project](http://ssix-project.eu/).
This project has received funding from the 
[European Union's Horizon 2020](https://ec.europa.eu/programmes/horizon2020/) 
research and innovation programme under grant agreement No 645425.