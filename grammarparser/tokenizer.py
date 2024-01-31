import re

def pre_tokenizer(log):
    tokens = re.split('(\W)', log)
    return tokens

def tokenizer(log):
    tokens = pre_tokenizer(log)