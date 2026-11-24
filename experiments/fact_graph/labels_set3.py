"""Hand labels for set 3, made after the code was frozen and before any checker ran on it. T agrees with the 10-Q;
F is wrong; U is not in the 10-Q; R is off only by rounding of rounded inputs; X is a list marker or not a claim."""
LABELS = {
    "bullbear2": {7: "TTTRTFTFFUTTTUUUU", 13: "TTT", 14: "T", 15: "T", 16: "TTR", 17: "TT", 18: "FTFTT", 19: "FTF",
                  20: "FT", 21: "FUF", 22: "FU", 23: "FTF", 24: "FTF", 25: "TTT", 26: "TTT", 30: "XFTTTTTTTT",
                  31: "XTTTTRR", 32: "XTT", 33: "XFTT", 37: "XTTTTT", 38: "XRTTTTFF", 39: "XTTTTTTTT",
                  40: "XTTTFFT", 41: "XTTTRTTTTTTR", 45: "UUUT", 46: "U"},
    "deck2": {9: "X", 11: "TTTT", 12: "RTTTT", 13: "TTTTTUUU", 14: "TTTT", 15: "UU", 17: "X", 21: "TTT", 22: "T",
              23: "T", 24: "TTTT", 25: "TT", 26: "TTTR", 27: "TTT", 28: "TT", 29: "TTT", 30: "TTT", 31: "TTT",
              32: "UUU", 33: "UU", 35: "TTT", 36: "TT", 37: "T", 39: "X", 43: "TTTTTTT", 44: "TTTTTRR",
              45: "TTTTTTT", 46: "TTTTTRT", 48: "TTTTT", 49: "TTT", 50: "T", 51: "TT", 52: "TTTT", 54: "X",
              56: "TTTT", 58: "TT", 59: "T", 60: "T", 61: "T", 62: "TT", 63: "TTTR", 65: "X", 67: "TTR",
              68: "TTTTT", 69: "TT", 70: "TT", 73: "X", 75: "UUUUTUU", 76: "TT", 77: "TT", 78: "TTTT", 86: "X",
              90: "TTTT", 91: "TTTTTT", 92: "TTTT", 93: "TTTTTT", 94: "TTTT", 95: "RTTTTT", 96: "T", 97: "TTX",
              98: "UUX", 99: "UUX", 100: "TTTTTT", 101: "TTX", 102: "TT", 103: "TTT", 104: "TTT", 105: "TTTT",
              106: "TTTTT", 108: "TTTT", 109: "TT", 113: "X", 115: "T", 117: "UU"},
    "recap": {8: "TTTTT", 9: "TTR", 10: "TT", 11: "FTF", 12: "FTF", 13: "FT", 14: "TTT", 15: "FTF", 16: "FTF",
              17: "FUF", 18: "FU", 22: "FTFTT", 23: "T", 24: "T", 25: "T", 31: "TTTTTT", 32: "TTTTTR",
              33: "TTTTTT", 34: "TTTTTR", 35: "TTTTTT", 37: "TTT", 39: "T", 46: "T", 47: "T", 48: "R", 49: "T",
              50: "TTT", 51: "TT", 52: "TT", 53: "TT", 54: "R", 56: "TT", 57: "FTT", 67: "UUUU", 69: "TT", 70: "TT",
              71: "TTTT", 72: "F", 78: "T", 79: "T", 80: "T", 85: "TTTF", 86: "TXTTT", 87: "TFTTT", 88: "T",
              91: "UU"},
}
