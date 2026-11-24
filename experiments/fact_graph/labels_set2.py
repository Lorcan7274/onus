"""Hand labels for the fresh briefs, made before any checker ran. T agrees with the 10-Q; F is wrong; U is not in
the 10-Q; R is off only by rounding of rounded inputs; X is a list marker or not a claim."""
LABELS = {
    "bullbear": {7: "TTTTTTFFFFTTUUTT", 13: "TTT", 14: "TTTTTT", 15: "TTTTTT", 16: "TTTTT", 17: "TT", 18: "FFTTF",
                 19: "FFTT", 20: "FFUU", 21: "FFTTFF", 22: "TTTTTR", 24: "TTT", 28: "XFFTTTTTTTTT", 29: "XTT",
                 30: "XTTTRRT", 31: "XTRTT", 32: "XTFFT", 36: "XTTTTTTUUUUU", 37: "XFFTTTT", 38: "XTTTTTTTTTT",
                 39: "XTFR", 40: "XTTFFR", 44: "UUU", 45: "UU", 47: "T"},
    "deck": {5: "X", 7: "TTTT", 8: "TTT", 9: "FFTTFF", 10: "FFTT", 13: "X", 17: "TTT", 18: "TTR", 19: "TT", 20: "FTF",
             21: "FTF", 22: "FT", 23: "FTF", 24: "FTF", 25: "FUF", 26: "FU", 28: "T", 30: "X", 32: "TTTT", 33: "TTTT",
             34: "TTTT", 35: "TTT", 36: "TTTR", 38: "X", 40: "FTT", 43: "TTTT", 44: "TTTT", 46: "X", 48: "TT",
             49: "TTTT", 50: "TT", 54: "X", 57: "UU", 58: "UUTUU", 62: "X", 64: "TTTT", 65: "TTTT", 66: "TTTTTF",
             67: "TFFF", 68: "TTTTT", 69: "TTF", 71: "X", 75: "UU", 76: "T"},
    "email": {12: "TTFU", 16: "TTTTTTTTTTFTFTFFTTFFTTT", 20: "TTTTTTT", 24: "TTRTTTTTT", 28: "UUUUTTUTTTTTFFX",
              32: "XUXUXX"},
}
