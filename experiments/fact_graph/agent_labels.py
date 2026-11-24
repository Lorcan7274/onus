"""Hand labels for every number in the three agent briefs, per line in row order.

T agrees with the 10-Q; F is wrong; U is not in the 10-Q; R is off only by rounding of rounded inputs;
X is a list marker."""
LABELS = {
    "haiku": {7: "TTTFFFTFUUTTTT", 13: "TTT", 14: "TTR", 15: "TT", 16: "FTF", 17: "FTF", 18: "FT", 19: "FTF", 20: "FT",
              21: "FUF", 22: "FU", 24: "TTTR", 26: "FFFTTTT", 32: "TTTTTT", 33: "TTTTRR", 34: "TTTTTT", 35: "TTTTRT",
              37: "TTTT", 41: "TTR", 42: "TTTTTTT", 43: "TT", 44: "TT", 45: "T", 49: "UUUUTUU", 51: "TTTTTTT",
              55: "XTT", 56: "XRRT", 57: "XTTTFF", 58: "XU", 59: "XTTTRT", 60: "XTR"},
    "opus": {7: "TTTTFFFFTUUTTT", 13: "TTT", 14: "TTT", 15: "TT", 16: "FTF", 17: "FTF", 18: "FT", 19: "FTF", 20: "FTF",
             21: "FUF", 22: "FU", 24: "FTFFTT", 25: "TTTT", 26: "TR", 32: "TTTTT", 33: "TTTTT", 34: "TTTTT",
             35: "TTTTT", 37: "TTTT", 38: "T", 39: "T", 41: "UT", 45: "TTTT", 46: "TTTTTT", 47: "TT", 53: "UUUU",
             54: "TTTTTTTT", 58: "TTTF", 59: "TTTT", 60: "T", 61: "TTT", 65: "X"},
    "sonnet": {7: "TTTFFFTTUUTTT", 13: "TTTT", 14: "TTTT", 15: "TT", 16: "FTF", 17: "FTFF", 18: "FT", 19: "FTF",
               20: "FTF", 21: "FUF", 22: "FU", 24: "TT", 25: "T", 26: "FTT", 27: "TT", 33: "TTTTT", 34: "TTTTT",
               35: "TTTTT", 36: "TTTTT", 38: "TTT", 42: "TRTTTT", 46: "TT", 47: "TTTTTT", 48: "TT", 49: "TT",
               53: "UU", 54: "UUTUU", 55: "TTTTTTTT", 60: "FTFTTT", 61: "TTTFTTT", 62: "TTTTTT",
               63: "FFTUUUUUUUTT", 64: "XXXXXUU"},
}
