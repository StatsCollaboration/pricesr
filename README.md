# pricesr

## Overview
Geary-Khamis code / revised and real-time indices and graphical comparison / Ken Van Loon (ken.vanloon@economie.fgov.be) 

## Contributing
Some guidelines...

## Naming Conventions
| Variable name       | Description    |  Class/Type    |
| ------------- |-------------|  -----|
| p      | price | double | 
| q      | quantity      |  double | 
| v | value, ie. p* q      | double |
| prod_id | value which uniquely identifies the product, eg. UPC, SKU, GTIN    | character | 
| t | period, eg. day, week, month or quarter     |  Date | 

## Structure
```
├── LICENSE
├── README.md          <- The top-level README for developers using this project.
├── data               <- Small test datasets in csv form. Alternatively, scripts to download hosted datasets.
└── src                <- The source code for calculating indexes.
```
