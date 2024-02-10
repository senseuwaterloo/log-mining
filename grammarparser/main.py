from tokenizer import BPE_tokenizer

logfile = '../data/passFile-aspell-e23675f5-a29f-427d-a6ad-7cc32d0c8c5a'

loglines = open(logfile).readlines()
tokenizer = BPE_tokenizer()

for line in loglines:
    tokens = tokenizer.pre_tokenizer(line)
    print(tokens)
    print(line)