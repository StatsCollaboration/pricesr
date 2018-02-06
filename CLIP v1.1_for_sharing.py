# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 08:39:52 2017

@author: Matthew Mayhew

Version: 1.1

Imputs: Dataset in long format with the following variables:
            date
            price
            unique ids
            class (i.e. apples)
            characteristics to cluster on (offer etc)
        base dates and end dates (needed for chaining)

"""
#%%

import pandas as pd
import numpy as np
import nltk as nl
import re
from fuzzywuzzy import fuzz
from sklearn.cluster import MeanShift
from sklearn.metrics import silhouette_score,silhouette_samples
from sklearn.tree import DecisionTreeClassifier
from scipy.stats import gmean 
#%%
##The offer_check function categorises the offers as offers may be unique to a product/store. 
def offer_check(dd):
    terms = ["buy","purchase","the"]
    for j in terms:
        if j in dd: 
            return "BOGO"         
    terms = ["off","was","save","half","now","only"] # perhaps add,only??
    for j in terms:
        if j in dd:
            return "Discount"
    terms = ["special purchase"]
    for j in terms:
        if j in dd: 
            return "Special Purchase"
    terms = ["add","get"]
    for j in terms:
        if j in dd: 
            return "add more"
    terms = ["clear","reduced"]
    for j in terms:
        if j in dd:
            return "reduced to clear"

## the produce_features applies the offer categorisation to the offer variable
def produce_features(df):
    df.loc[:,"offer"] =df["offer"].apply(lambda x: str(x))
    df.loc[:,"offer"] =df["offer"].apply(lambda x: x.lower())
    df.loc[:,"offer_cat"] =df["offer"].apply(lambda x: offer_check(x))
    return df

##this function tokenises and manipuates the strings into easier ways for the following functions
stemmer = nl.stem.PorterStemmer()
def normalize(s):
    words = nl.tokenize.wordpunct_tokenize(s.lower().strip())
    return ' '.join([stemmer.stem(w) for w in words])



#this function puts the dataframe in the right format for the 
#clusting to work, this would need to be adapted for each characteristics, if the characterist is numeric leave as a numeric, is factor then create dummies.
def manipulate(data,datevar,pricevar):
    df_new = pd.DataFrame()
    #create dummy variable for store and offer type
    shops = pd.get_dummies(data["store"])
    offercat = pd.get_dummies(data["offer_cat"])
    df_new["product_name"]=data["idvar"]
    df_new["item_name"]=data["item_name"]
    #set freq variable
    df_new["monthday"] = data[datevar]
    #set price type
    df_new["price"] = data[pricevar]
    #remove 0 or non-numeric prices
    df_new = df_new[np.isfinite(df_new['price'])]
    #group together the dataframe for later use
    df_new = pd.concat([df_new,shops,offercat],axis=1)
    df_new["product_name"]=df_new["product_name"].astype("str")
    df_new["product_name"]=df_new["product_name"].apply(lambda s: normalize(s))
    df_new["product_name"]=df_new["product_name"].apply(lambda s: re.sub(r'[^\w\s]','',s))
    t=re.sub(r'[^\w\s]','',normalize(pd.unique(df_new["item_name"])[0]))
    #edit distance between ons item name and the product name 
    df_new.loc[:, 'prod_no'] = df_new["product_name"].apply(lambda s: fuzz.ratio(s,t))
    print(df_new.head(2))
    df_new=df_new.drop_duplicates(["product_name","monthday"])
    print(len(df_new))
    return df_new



##finding clusters in the base date

def base_clusters(data,basedate):
    basemonth=data[data["monthday"]==basedate]
    #deleting columns we don't want to cluster over 
    data3 = basemonth
    #reduce dataframe to the variables that will be used within the dbscan clustering (price is included here)
    del data3["item_name"]
    del data3["product_name"]
    del data3["monthday"]
    #remove duplicates so that clustering is only on unique products. This stops grouping togepthers of the same product
    data3 = data3.drop_duplicates()
    ward = MeanShift(cluster_all=True, n_jobs=-1).fit(data3)
    data3["cluster"]=ward.labels_
    return data3
    
##creates the decision tree and then applies it in non base dates, note price is removed as a characteristic

def DecisionTree(data,basemonth,basedate,dates):
    data1=pd.DataFrame()
    if len(basemonth) < 100:
        dlen = 8
    else:
        dlen = int(np.floor(len(basemonth)/15))  
    DT=DecisionTreeClassifier(criterion = "gini", min_samples_leaf=dlen)
    c=list(basemonth.columns)
    c=c[2:(len(c)-1)]
    dt = DT.fit(basemonth[c],basemonth['cluster'])
    d=list(data.columns)
    d=d[4:len(d)]
    d.append("monthday")
    for date in dates:
        print(date)
        APD=data[data["monthday"]==date]
        predLab=dt.predict(APD[c])
        APD["cluster"]=predLab
        data1=data1.append(APD)
    return data1

#calculation of the clip index from clusters that were already formed earlier
def CLIP_calc(data,basedate):
    z=data.groupby(["cluster","monthday"]).agg({'price':gmean,'cluster':len})
    z=z[['price', 'cluster']]
    z.columns=["price","count"]
    z=z.reset_index()
    weights=z[z["monthday"]==basedate][["cluster","count"]]
    weights["count"]=weights["count"]/weights["count"].sum()
    price=pd.pivot_table(z, index="cluster",columns="monthday",values="price")
    col=price.columns.values
    #loop through all periods as base
    base=col[0]
    ## create coppies of y to work on 
    B = price.copy()
    B1 = price.copy()
    #divide each column by base column
    for date in col:        
        B[date] =B1[date] / B1[base]   ## generate your relatives
    
    B=B.reset_index()
    
    B=B.merge(weights,on="cluster")
    
    B2=B.copy()
    for date in col:
        B2[date] =B[date] * B["count"] 
    
    CLIP=B2.sum(axis=0)
    Indices=CLIP.reset_index()
    Indices.columns=["monthday","Index"]
    Indices=Indices[Indices["monthday"]!="cluster"][Indices["monthday"]!="count"]
    Indices["Type"]="CLIP"
    return(Indices)

#calculates a unit value if there isn't enough data to cluster
def Unit_Value(data):
    price=pd.pivot_table(data, index='product_name',columns="monthday",values="price")
    col=price.columns.values
    #loop through all periods as base
    col=price.columns.values
    #loop through all periods as base
    base=col[0]
    ## create coppies of y to work on 
    B = np.exp(np.log(price).mean())
    B1 = B.copy()
    #divide each column by base column
    for date in col:        
        B1[date] =B[date] / B[base]   ## generate your relatives
    B1=B1.reset_index()
    B1.columns=["Date","Index"]
    B1["Type"]="Unit Value"
    return(B1)

##main wrapper function to calculate indices within a year you would need to change the data in the base date and enddate for other time periods
def CLIP(data,basedate,enddate,pricevar):
    if basedate in [201406,201501,201601,201701,201423]:
        if enddate in [201501,201601,201701,201703,201713]:
            if "month" in data.columns:
                df=data[data["month"]>=basedate][data["month"]<=enddate]
                df=produce_features(df)
                df["idvar"]=df["product_name"]+"_"+df["store"]
                df=manipulate(df,"month",pricevar)
            elif "week" in data.columns:
                df=data[data["week"]>=basedate][data["week"]<=enddate]
                df=produce_features(df)
                df["idvar"]=df["product_name"]+"_"+df["store"]
                df=manipulate(df,"week",pricevar)
            print(np.unique(df["item_name"]).item())
            bm=df[df["monthday"]==basedate]
            if max(bm.nunique())>30:
                bc=base_clusters(df,basedate)
                dates=list(pd.unique(df["monthday"].values))
                dates.sort()
                dt=DecisionTree(df,bc,basedate,dates)
                results=CLIP_calc(dt,basedate)
            elif max(bm.nunique())<30:
                results=Unit_Value(df)
                dates=list(pd.unique(df["monthday"].values))
                dates.sort()
                results["monthday"]=dates
            results["Item"]=np.unique(df["item_name"]).item()
            return(results)
        else:
            print("Error End Period is not a legal parameter")
    else:
        print("Error Base Period is not a legal parameter")

#functions to do the chaining first one does the chaining the second does the data prep the chains
def chain(h,basedate2,basedate3,basedate4):
    h["factor1"]=1
    h["factor2"]=1
    h["factor3"]=1
    fact1=float(h["Index"][h["monthday"]==basedate2])
    fact2=float(h["Index"][h["monthday"]==basedate3])
    fact3=float(h["Index"][h["monthday"]==basedate4])
    for j in range(len(h)):
        if h.loc[j,"monthday"]>basedate2:
            h.loc[j,"factor1"]=fact1
        if h.loc[j,"monthday"]>basedate3:
            h.loc[j,"factor2"]=fact2
        if h.loc[j,"monthday"]>basedate4:
            h.loc[j,"factor3"]=fact3
    h["chained"]=h["Index"]*h["factor1"]*h["factor2"]*h["factor3"]
    return(h)
    
def chain_clip(df1,df2,df3,df4,basedate2,basedate3,basedate4):
    df2=df2[df2["monthday"]!=basedate2]    
    df3=df3[df3["monthday"]!=basedate3]    
    df4=df4[df4["monthday"]!=basedate4]    
    h=df1.append(df2).append(df3).append(df4).reset_index()
    h1=chain(h,basedate2,basedate3,basedate4)
    return(h1)

