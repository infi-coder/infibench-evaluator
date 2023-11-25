#输入一个list,返回按照字母序排序后的结果
library(assert)
f <- function(list_text_data){
    result <- list_text_data[order(names(setNames(list_text_data, list_text_data)))]
    return (result)
}
mySort <- function(list_text_data){
    result <- list_text_data[order(names(setNames(list_text_data, list_text_data)))]
    return (result)
}
l1 = c(5, 4, 3, 2, 1, 2, 3, 4, 5)
l2 = c('1', 'a', 'x', 'ad', 'gsf', 'dfha', 'aaa')
df1 = f(l1)
df2 = mySort(l1)
df1 = unname(df1)
df2 = unname(df2)
assert(identical(df1, df2))


df1 = f(l2)
df2 = mySort(l2)
df1 = unname(df1)
df2 = unname(df2)
assert(all.equal(df1, df2, check.attributes = FALSE))
