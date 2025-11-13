set -e
set -u

# MAD_PATH=$(realpath `dirname $0`)
MAD_PATH=/eecs-498/MAD_10_27/Multi-Agents-Debate

python3 $MAD_PATH/code/debate4tran.py \
    -i $MAD_PATH/data/CommonMT/input.example.txt \
    -o $MAD_PATH/data/CommonMT/output \
    -lp zh-en \
    -k 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 \
