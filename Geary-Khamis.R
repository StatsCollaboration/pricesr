# Geary-Khamis code / revised and real-time indices and graphical comparison / Ken Van Loon (ken.vanloon@economie.fgov.be) / April - 2018
if (!require('dplyr')) install.packages('dplyr'); library('dplyr')
#change this to your directory (forward slashes!)
setwd("C:/blablabla")
dataset <- read.csv("artificial_test_data.csv") %>%  mutate(t = as.Date(t, format = '%d/%m/%Y')) %>% arrange(t, prod_id)
#######################################################################################
#calculate using all available periods to get final index incl. the non-"real time" indices of previous months
test_qu <- dataset %>% group_by(prod_id) %>% mutate(PHI=q/sum(q), P=1, P_PREV=0, v=q*p) %>% group_by(t) %>% mutate(SUM_v=sum(v))
test_qu$V_I <- test_qu$SUM_v/test_qu$SUM_v[1]
i<-0
while (!isTRUE(all.equal(round(test_qu$P_PREV, 5),round(test_qu$P, 5))))  {
  i <- i+1
  test_qu <- test_qu %>% mutate(P_PREV=P, VI=(p/P)*PHI) %>% group_by(prod_id) %>% mutate(VI=sum(VI), QAV=VI*q) %>% group_by(t) %>% mutate(SUM_QAV=sum(QAV))
  test_qu$Q_I <- test_qu$SUM_QAV/test_qu$SUM_QAV[1]
  test_qu$P <- test_qu$V_I/test_qu$Q_I
}
print(paste0("number of iterative steps: ",i))
final_index <- unique(subset(test_qu, select = c(t,P)))
#######################################################################################
#calculate using "incremental" ("real-time") approach with all available periods, final index will be the same as in the previous calculation
individual_months <- unique(dataset$t)
final_index_real_time <- NULL
iterations_overview <- NULL
for (k in 1:(length(individual_months)-1)){
  test_qu <- dataset %>% filter(t %in% individual_months[0:k+1]) %>% group_by(prod_id) %>% mutate(PHI=q/sum(q), P=1, P_PREV=0, v=q*p) %>% group_by(t) %>% mutate(SUM_v=sum(v))
  test_qu$V_I <- test_qu$SUM_v/test_qu$SUM_v[1]
  i<-0
  while (!isTRUE(all.equal(round(test_qu$P_PREV, 5),round(test_qu$P, 5))))  {
    i <- i+1
    test_qu <- test_qu %>% mutate(P_PREV=P, VI=(p/P)*PHI) %>% group_by(prod_id) %>% mutate(VI=sum(VI), QAV=VI*q) %>% group_by(t) %>% mutate(SUM_QAV=sum(QAV))
    test_qu$Q_I <- test_qu$SUM_QAV/test_qu$SUM_QAV[1]
    test_qu$P <- test_qu$V_I/test_qu$Q_I
  }
  temp_index <- unique(subset(test_qu, select = c(t,P)))
  colnames(temp_index) <- c("t", paste0("P",k))
  if (k>1) {
    final_index_real_time <- merge(final_index_real_time,temp_index, by="t", all.y=TRUE)
  } else {
    final_index_real_time <- temp_index
  }
  iterations_overview_temp <- data.frame(t=k,iterations=i)
  iterations_overview <- rbind(iterations_overview, iterations_overview_temp)
  rm(test_qu)
}
rm(iterations_overview_temp, temp_index)
#######################################################################################
#simple graph comparing actual vs real time index
real_time <- as.data.frame(do.call(rbind, lapply(1:length((individual_months)-1), function(x)  final_index_real_time[x+1,x+1])))
colnames(real_time) <- "P"
real_time <- data.frame(final_index[,"t"],rbind(data.frame(P=1),real_time),TYPE="REAL-TIME")
final <- data.frame(final_index, TYPE="FINAL")
comparison <- rbind(real_time,final)
rm(real_time,final)
ggplot(data=comparison,
       aes(x=t, y=P, colour=TYPE)) +
  geom_line()
