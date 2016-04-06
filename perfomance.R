## FUNCTIONS
#---------------------------------------------------------------------

returnToDailyReturn <- function(x){
  #x - irregular returns
  
  ret = data.frame()
  for (i in 1:(length(x) - 1)){
    
    #days between two returns
    dift = difftime(index(x[i + 1]), index(x[i]), units = 'days')
    
    #daily return
    ret[i,1] = (x[i+1] / as.double(dift))
  }
  colnames(ret) <- colnames(x)
  return(xts(ret, order.by = index(x[-1])))
}

profitFactor <- function(x){
  #x - portfolio,$
  
  #delta,$
  dif = diff(x)
  
  #gross profit
  plus = sum(ifelse(dif > 0, dif, 0), na.rm = TRUE)
  
  #gross loss
  minus = sum(ifelse(dif < 0, dif, 0), na.rm = TRUE)
  
  return(abs(plus / minus))
}

maxDD <- function(x, y){
  #x - irregular returns
  #y - portfolio,$
  
  #get first MDD,%
  dd = table.Drawdowns(x, top = 1)
  
  #get from to till dates of MDD,%
  from = as.character(dd$From[1])
  trough = as.character(dd$Trough[1])
  
  mdd = coredata(y[trough]) - coredata(y[y[from, which.i = TRUE] - 1])
  return(abs(mdd))
}

netProfit <- function(x){
  #x - portfolio,$
  
  return(coredata(last(x)) - coredata(first(x)))
}

percentReturn <- function(x){
  #x - portfolio,$
  return(coredata(last(x)) / coredata(first(x)) - 1)
  
}

payoffRatio <- function(x){
  #x - daily return
  
  #positive returns
  p = x[x > 0,]
  
  #negative returns
  n = x[x < 0,]
  
  return((sum(coredata(p)) / length(p)) / abs(sum((coredata(n))) / length(n)))
}

cagr <- function(x){
  #daily CAGR, not annual
  #x - portfolio,$
  
  (coredata(last(x)) / coredata(first(x)))^(1 / 0.25) - 1
}


## CALCULATIONS
#-----------------------------------------------------------------------
require(xts)
require(PerformanceAnalytics)


#make empty xts with date index
kapital <- xts(order.by = as.Date('2015-09-15') + 0:91)
marja <- xts(order.by = as.Date('2015-09-15') + 0:91)
dohodnost <- xts(order.by = as.Date('2015-09-15') + 0:91)

#list of files with equity
files <- list.files('./data/', pattern = '*.csv', full.names = TRUE)

perfomance <- matrix(nrow = 11, ncol = length(files))
rownames(perfomance) <- c('CAGR','Return','MDD','Recovery factor',
                          'Profit factor','Payoff ratio', 'Sharp ratio',
                          'Sortino ratio','MAR','R2', 'len data')


for (i in seq_along(files)){
  csv_ <- read.csv2(file       = files[i], 
                    colClasses = list('character','character'),
                    header     = FALSE)
  
  xts_ <- xts(x        = as.numeric(csv_[,2]), 
              order.by = as.POSIXct(csv_[,1]), 
              unique   = FALSE)
  #xts_ <- xts_2['/2015-11-13']
  
  kap <- to.daily(xts_, indexAt   = 'endof', drop.time = TRUE)[,4]
  
  #set column names = 't'+id, trader id from file name:
  dimnames(kap) <- list(NULL, paste0('t', substring(files[i],8,12)))
  
  kapital <- merge.xts(kapital, kap, join = 'outer')
  
  marj <- Return.calculate(kap)
  marja <- merge.xts(marja, marj, join = 'outer')
  #charts.PerformanceSummary(marj)
  
  doh <- returnToDailyReturn(marj)
  dohodnost <- merge.xts(dohodnost, doh, join = 'outer')
  
  #dimnames(marj) <- list(NULL, paste0('t', substring(lf[i],8,12)))
  #dimnames(doh) <- list(NULL, paste0('t', substring(lf[i],8,12)))
  
  
  #CAGR,%
  perfomance[1,i] <- cagr(kap) * 100
  
  #Return,%
  perfomance[2,i] <- percentReturn(kap) * 100
  
  #Maximum drawdown,%
  perfomance[3,i] <- table.DownsideRisk(marj)[7,] * 100
  
  #Recovery factor
  perfomance[4,i] <- netProfit(kap) / maxDD(marj, kap)
  
  #Profit factor
  perfomance[5,i] <- profitFactor(kap)
  
  #Payoff ratio
  perfomance[6,i] <- payoffRatio(doh)
  
  #Sharpe ratio
  perfomance[7,i] <- SharpeRatio(doh, p = 0.99, FUN = 'StdDev') * 365^.5
  
  #Sortino ratio
  perfomance[8,i] <- SortinoRatio(doh) * 365^.5
  
  #MAR ratio
  perfomance[9,i] <- cagr(kap) / table.DownsideRisk(marj)[7,]
  
  #R2
  perfomance[10,i]<- summary(lm(kap ~ seq(1:length(kap))))$r.squared
  
  #Length
  perfomance[11,i]<- length(marj)
  
}


#name for columns
colnames(perfomance) <- paste0('t', substring(files,8,12))

t_perf <- t(perfomance)
colnames(t_perf) <- c('CAGR','Return','MDD','Recovery factor',
                      'Profit factor','Payoff ratio', 'Sharp ratio',
                      'Sortino ratio','MAR','R2', 'len data')

write.csv2(t_perf, 'perform.csv')
           
           

## TRASH
#-----------------------------------------------------------------

install.packages('quantmod_0.4-5.zip', repos=NULL, type = 'source')


charts.PerformanceSummary(ret2)

table.Stats(ret)

chart.QQPlot(ret)

chart.Histogram(ret)

chart.Histogram(ret, main = "Density", breaks=40,
                methods = c("add.density", "add.normal"))



table.DownsideRisk(ret2)
table.Drawdowns(ret2)
table.DrawdownsRatio(ret2)
table.Stats(ret2)
Return.cumulative(ret2, geometric = T) 


Return.annualized(ret2)
Return.annualized(ret, geometric = F) 
mean.geometric(ret)
SharpeRatio(ret, p = 0.99)
SharpeRatio.annualized(ret2, geometric=T) ### это Шарп
SortinoRatio(ret) 




charts.PerformanceSummary(id55150.ret)
table.DownsideRisk(id55150.ret)
SharpeRatio(id55150.ret, p = 0.99)
SharpeRatio.annualized(id55150.ret, geometric=T)
SortinoRatio(id55150.ret)
table.Stats(id55150.ret)
chart.Histogram(id55150.ret)
mean(id55150.ret, na.rm=TRUE)






