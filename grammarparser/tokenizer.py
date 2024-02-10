import re

class BPE_tokenizer:
    def __init__(self):
        # dict to store the map between the normalized words and original words
        self.word_case_dicts = {}
        pass

    def pre_tokenizer(self, log):
        tokens = re.split('(\W)', log)
        tokens.remove('\n')
        tokens = list(filter(None, tokens))
        return tokens

    def normalizer(self, tokens):
        tokens_normalize_map = {}
        for token in tokens:
            token_normalize = token.lower()
            tokens_normalize_map[token] = token_normalize
        self.word_case_dicts.append(tokens_normalize_map)

    def tokenizer(self, log):
        tokens_pre = self.pre_tokenizer(log)