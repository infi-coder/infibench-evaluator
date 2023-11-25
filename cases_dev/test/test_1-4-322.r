library(tidyverse)

f <- function(my_data){
    return (my_data |>
      group_by(list_names)  |>
      group_modify(\(x, ...) tibble(res = list(deframe(x)))) |>
      deframe())
}

my_data <- tibble(list_names = c("Ford", "Chevy", "Ford", "Dodge", "Dodge", "Ford"),
                    list_values = c("Ranger", "Equinox", "F150", "Caravan", "Ram", "Explorer"))

library(assert)

assert(all.equal(f(my_data), myConvert(my_data), check.attributes = FALSE))
