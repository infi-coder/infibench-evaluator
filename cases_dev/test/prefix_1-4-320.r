# 创建一个100行、1000列的数据框
library(dplyr)
n_rows <- 100
n_cols <- 1000
final <- as.data.frame(matrix(NA, nrow = n_rows, ncol = n_cols))

final[10:20, 490] <- 1
final[40:50, 100] <- 21
final[60:70, 550] <- 31
final[8, 556] <- 40
final[3, 455] <- 1100
final[99, 400:500] <- 11
final[95, 300:600] <- 1100