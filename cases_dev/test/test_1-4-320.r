
library(dplyr)

# 创建一个100行、1000列的数据框
n_rows <- 100
n_cols <- 1000
df <- as.data.frame(matrix(NA, nrow = n_rows, ncol = n_cols))

df[10:20, 490] <- 1
df[40:50, 100] <- 21
df[60:70, 550] <- 31
df[8, 556] <- 40
df[3, 455] <- 1100
df[99, 400:500] <- 11
df[95, 300:600] <- 1100


x <- df %>% filter(!if_all(V456:V555, is.na))
library(assert)
assert(all.equal(final, x, check.attributes = FALSE))