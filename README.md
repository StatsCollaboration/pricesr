# CLIP

## Overview
This repository is intended to host the python code for the construction of the CLIP Index. Developed by Matt Mayhew - Email Matthew.Mayhew@ons.gov.uk if help needed. [A description of the method can be found here](https://www.ons.gov.uk/economy/inflationandpriceindices/articles/researchindicesusingwebscrapedpricedata/clusteringlargedatasetsintopriceindicesclip) with some properites explored [here](https://www.ons.gov.uk/methodology/methodologicalpublications/generalmethodology/onsworkingpaperseries/onsmethodologyworkingpaperseriesnumber12acomparisonofindexnumbermethodologyusedonukwebscrapedpricedata) 

## Contributing
Some guidelines...

## Naming Conventions
| Variable name       | Description    |  Class/Type    |
| ------------- |-------------|  -----|
| price      | price | double | 
| store      | store/shop      |  string | 
| offer |  if there is an offer/discount     | double |
| product_name | the name of the product in full    | character | 
| period | period, eg. day, week, month or quarter     |  Date | 
| product | unique code for each product | string or double |
| item_name | the item to which the product belongs | string |

## Example files 

In the data foler there are two files: 

 * CLIP_example_data.csv - this is the file format for imputing into the CLIP code. Note that the prices are randomly generated to have a linear trend. 
 * CLIP_example_after_clustering.csv - this is the output when the data has be processed and the base clusters have been formed. 

## Structure
```
????????? LICENSE
????????? README.md          <- The top-level README for developers using this project.
????????? data               <- Small test datasets in csv form. Alternatively, scripts to download hosted datasets.
????????? src                <- The source code for calculating indexes.
```
