#!/bin/bash
set -e
set -u

# MAD_PATH=$(realpath `dirname $0`)
# MAD_PATH=/eecs-498/MAD_10_27/Multi-Agents-Debate

python3 ./code/debate4math.py \
    -i ./data/CounterintuitiveQA/input.txt \
    -o ./data/CounterintuitiveQA/outputs_sonnet \
    -k <Enter API Key> \

# #!/bin/bash
# set -e
# set -u

# # MAD_PATH=$(realpath `dirname $0`)
# MAD_PATH=/eecs-498/MAD_10_27/Multi-Agents-Debate

# python3 $MAD_PATH/code/debate4math.py \
#     -i $MAD_PATH/data/CounterintuitiveQA/input_small.txt \
#     -o $MAD_PATH/data/CounterintuitiveQA/outputs \
#     -k <Enter API Key> \