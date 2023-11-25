
f <- function(df1){
    out <- type.convert(as.data.frame( read.dcf(textConnection(paste(gsub(",", "\n", df1$col1), collapse = "\n\n"))) ), as.is = TRUE)
    return(out)
}

df = data.frame(col1=c('name:Miqchael,Age:31,City:NYC','name:Tom,Age:25,City:AA','name:A,Age:36,City:AAS'))

df1 <- f(df)

df2 <- mySplit(df)

assert(all.equal(df1, df2, check.attributes = FALSE))

