# setting up javascript and typescript env
apt-get install -y nodejs
mkdir ~/.npm-global
npm config set prefix `~/.npm-global`
source ~/.profile
export PATH=~/.npm-global/bin:$PATH
npm install -g jsdom
npm install -g typescript
export NODE_PATH=$(npm root --quiet -g)
# setup c# env:
apt-get install -y mono-complete
# setup go env:
apt-get install -y golang-go
# setup r env:
apt-get install -y r-base
apt-get install -y r-base-dev
apt-get install -y libssl-dev
apt-get install -y libfontconfig1-dev
apt-get install -y libcurl4-openssl-dev
apt-get install -y libxml2-dev
apt-get install -y libharfbuzz-dev
apt-get install -y libfribidi-dev
apt-get install -y libfreetype6-dev libpng-dev libtiff5-dev libjpeg-dev
Rscript -e 'install.packages("assert")'
Rscript -e 'install.packages("stringr")'
Rscript -e 'install.packages("tidyverse")'
Rscript -e 'install.packages("dplyr")'
Rscript -e 'install.packages("data.table")'

# for bigcode-evaluation-harness
# export DATASET_CSV_PATH=xxxxx/open-freeform-code-qa-suite/batched_prompts/suite_v2.0.0.csv