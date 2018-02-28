#Author:
#Ross Beck-MacNeil
#Statistics Canada - Consumer Prices Divsion
#ross.beck-macneil@canada.ca

#How to Use:
#This is a very preliminary version
#It might not run under a non-windows environment
#It needs
#Since it does not products any output files at the moment

#This is reason why it might not run in non-windows environment
#If running interaactively or with an OS where this doesn't work, needs to be specified
this.dir <- dirname(parent.frame(2)$ofile)
setwd(this.dir)

#Specify desired window size here
# Normally a year + a period, so 4 for quarters and 13 for months
# Better code would allow also 0/NULL/unspecified in order to
window_size = 13



library(data.table)

#Read in data
df = fread("artificial_test_data.csv")

#1. a little bit of cleaning and preparation
df[,value:=p*q]

#log prices
df[,log_p := log(p)]

#Expenditure shares by month
df[,share := value/sum(value), by = t]

#map dates to an integer
#not really necessary, but was in NZ SAS code
#better handling of dates should be implemented in the future
periods = df[,unique(t)]
period_as_int <- function(t){
  #referring to a global here, not good form
  return(match(t, periods))
}
#
df[, period_n := period_as_int(t)]

n_movements = window_size-1

last.period = length(periods)

#periods start at 1 and incrment by 1 up to max (last period)
start_periods = 1:(last.period-n_movements)

#should create a class or something...
#precreate data.table for results
FEWS = data.table(periods = (1:last.period), index = rep(0, length(periods)))
#and window indexes
window_indexes = list()
# and splice factor...
splice.factor = 1

#iterate through all possible start periods
for (i in start_periods) {

  #get inlcuded periods and create orderered character (from integer)
  window.periods = seq(from = i, by = 1, length.out = window_size)

  #create window - is easier
  window = df[period_n %in% window.periods,]
  setorder(window, "prod_id")
  window[,period_f := factor(as.character(period_n),as.character(window.periods))]
  
  #similar to SAS, rather than explicilty including dummies for products
  #"sweep out" or "absorb their fixed effects first....
  dummies = model.matrix( ~ period_f -1, data=window[,.(period_f)])
  dummy.names = dimnames(dummies)[[2]]
  demean.variables = c("log_p", dummy.names)
  
  model.variables = data.table(dummies, window[,.(prod_id,log_p,share)])
  
  model.variables[, (demean.variables) := lapply(.SD, function(x) x - weighted.mean(x,share)), by = prod_id,
         .SDcols = demean.variables]
  
  #kind of weird way of making sure only time dummies are used in regression
  formula.inclusions = paste(dummy.names, collapse = " + ")
  formula = as.formula(paste(c("log_p ~ ", formula.inclusions, " -1"), collapse = ""))
  
  regression = lm(formula, data = model.variables, weights = model.variables$share)
  coeffs = coefficients(regression)
  #calculate period over period movements
  #first period has no movement (since no back period, is base)
  #currently last period is always implicitly dropped by lm, so is reference (i.e 0)
  #but should put in something more robust and explicit
  #pop_movements = c(coeffs[1:n_movements],0) - c(coeffs[1],coeffs[1:n_movements])
  window_indexes[[i]] = exp(c(coeffs[1:n_movements],0) - coeffs[1])
  
  
  
  if (i==1){ #if first window, want indexes for whole window
    FEWS[window.periods,index:= window_indexes[[1]]]
  } else { #if not first period, need last index for current window X splice factor
    #previous index
    #extra closing brackets are cause of bug in data.table that hinders printing
    #after returning from a function (or loop?)
    FEWS[i+n_movements,index:= window_indexes[[i]][window_size] * splice.factor][]
  }
  splice.factor = splice.factor * window_indexes[[i]][2]
}

fwrite(FEWS, "out.csv")