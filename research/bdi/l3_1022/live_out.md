# Live paper record - L3-gap-slope-fromopen-FD (through 2026-10-22)

## primary: {'trades': 23, 'sessions': 2, 'win_pct': 39.1, 'breakeven_win_pct': 55.4, 'avg_r': -0.308, 't': -1.19, 'pnl_adj': -192.05, 'sum_r': -7.07, 'last4_avg_r': -0.308, 'last4_pnl': -192.05, 'first': '2026-10-21', 'last': '2026-10-22'}
                  n      R   avgR     pnl  regime  syms  maxlots
date       acct                                                 
2026-10-21 p      5 -5.747 -1.149 -176.93  Choppy     2        3
2026-10-22 p     18 -1.326 -0.074  -15.12  Choppy     5        7

by regime:
       trades sessions win_pct breakeven_win_pct  avg_r sum_r pnl_adj
Choppy     23        2    39.1              55.4 -0.308 -7.07 -192.05

by lot number (1, 2, 3+ within symbol-day):
  trades win_pct  avg_r sum_r pnl_adj
1      7    28.6 -0.807 -5.65 -131.45
2      7    28.6 -0.511 -3.58 -114.01
3      9    55.6   0.24  2.16   53.41

by entry time:
            trades win_pct  avg_r sum_r pnl_adj
09:50-10:30      1   100.0  0.363  0.36   22.08
10:30-11:30      8    37.5 -0.653 -5.22 -104.84
11:30-13:00     14    35.7 -0.158 -2.21 -109.29

symbol-days with >= 2 lots: 7 of 7, R -7.07, $-192.05
                   lots     R     pnl
date       symbol                    
2026-10-22 JBS        3 -3.96  -68.16
2026-10-21 FTNT       3 -3.23  -58.10
           TKNO       2 -2.52 -118.83
2026-10-22 IBX        2 -0.11  -10.63
           LI         3  0.07    1.63
           FMC        3  0.83   51.58
           SNAP       7  1.85   10.46

## testing1: {'trades': 128, 'sessions': 6, 'win_pct': 64.1, 'breakeven_win_pct': 51.1, 'avg_r': 0.197, 't': 1.04, 'pnl_adj': 527.11, 'sum_r': 25.25, 'last4_avg_r': 0.237, 'last4_pnl': 510.7, 'first': '2026-10-13', 'last': '2026-10-20'}
                  n       R   avgR     pnl  regime  syms  maxlots
date       acct                                                  
2026-10-13 t1    15  -0.541 -0.036   13.90   Quiet    15        1
2026-10-14 t1     6   0.380  0.063    2.51    Bear     3        4
2026-10-15 t1    12 -13.524 -1.127 -188.31    Bull     8        3
2026-10-16 t1     8   2.395  0.299   10.44    Bear     2        6
2026-10-19 t1     7   2.935  0.419   33.60   Quiet     2        5
2026-10-20 t1    80  33.603  0.420  654.97  Choppy    25        5

by regime:
       trades sessions win_pct breakeven_win_pct  avg_r  sum_r pnl_adj
Bear       14        2    57.1              47.6  0.198   2.78   12.95
Bull       12        1     0.0              None -1.127 -13.52 -188.31
Choppy     80        1    77.5              39.0   0.42   33.6  654.97
Quiet      22        2    54.5              48.5  0.109   2.39    47.5

by lot number (1, 2, 3+ within symbol-day):
  trades win_pct  avg_r  sum_r pnl_adj
1     55    56.4  0.067   3.68  114.31
2     31    64.5  0.192   5.95   83.43
3     42    73.8  0.372  15.62  329.38

by entry time:
            trades win_pct  avg_r  sum_r pnl_adj
09:50-10:30     10    60.0  0.093   0.93   31.25
10:30-11:30     60    66.7   0.19  11.43  302.52
11:30-13:00     49    63.3  0.266  13.02  185.99
13:00-14:30      8    50.0  -0.11  -0.88   -5.94
14:30-15:00      1   100.0   0.75   0.75    13.3

symbol-days with >= 2 lots: 31 of 55, R +29.71, $+550.60
                   lots     R    pnl
date       symbol                   
2026-10-15 CRCL       3 -3.08 -36.92
2026-10-20 OUST       3 -2.63 -54.87
2026-10-15 BULL       2 -2.30 -46.02
           USAR       2 -2.18 -29.94
2026-10-20 NBIS       3 -1.09 -25.46
           AXTI       3 -0.86 -25.28
2026-10-14 AVEX       4 -0.67  -6.23
2026-10-20 CIFR       3 -0.65 -19.61
           QNT        3 -0.61 -14.68
           FLNC       3  0.28   6.94
           NVTS       3  0.38   9.39
2026-10-16 FMC        6  0.38  -0.15
2026-10-20 SMR        3  0.47   9.81
           COHR       3  0.48   8.44
2026-10-19 SOXS       5  0.54  13.59
2026-10-20 OKLO       3  0.65  11.55
           HPE        3  0.81  12.49
           SOXL       3  1.28  35.93
           AAOI       3  1.34  37.40
2026-10-16 TLK        2  2.02  10.59
2026-10-20 RIOT       3  2.15  48.77
2026-10-19 TLK        2  2.39  20.01
2026-10-20 PENG       3  2.67  68.85
           RCUS       3  2.89  31.12
           CRWV       3  2.94  55.36
           INFQ       4  3.08  54.27
           ALM        5  3.39  72.71
           WULF       5  3.41  73.67
           APLD       4  3.43  67.34
           CORZ       4  4.32  68.39
           CLSK       5  4.47  93.14

## all: {'trades': 151, 'sessions': 8, 'win_pct': 60.3, 'breakeven_win_pct': 52.7, 'avg_r': 0.12, 't': 0.62, 'pnl_adj': 335.06, 'sum_r': 18.18, 'last4_avg_r': 0.268, 'last4_pnl': 496.52, 'first': '2026-10-13', 'last': '2026-10-22'}
                  n       R   avgR     pnl  regime  syms  maxlots
date       acct                                                  
2026-10-13 t1    15  -0.541 -0.036   13.90   Quiet    15        1
2026-10-14 t1     6   0.380  0.063    2.51    Bear     3        4
2026-10-15 t1    12 -13.524 -1.127 -188.31    Bull     8        3
2026-10-16 t1     8   2.395  0.299   10.44    Bear     2        6
2026-10-19 t1     7   2.935  0.419   33.60   Quiet     2        5
2026-10-20 t1    80  33.603  0.420  654.97  Choppy    25        5
2026-10-21 p      5  -5.747 -1.149 -176.93  Choppy     2        3
2026-10-22 p     18  -1.326 -0.074  -15.12  Choppy     5        7

by regime:
       trades sessions win_pct breakeven_win_pct  avg_r  sum_r pnl_adj
Bear       14        2    57.1              47.6  0.198   2.78   12.95
Bull       12        1     0.0              None -1.127 -13.52 -188.31
Choppy    103        3    68.9              50.4  0.258  26.53  462.92
Quiet      22        2    54.5              48.5  0.109   2.39    47.5

by lot number (1, 2, 3+ within symbol-day):
  trades win_pct  avg_r  sum_r pnl_adj
1     62    53.2 -0.032  -1.97  -17.14
2     38    57.9  0.062   2.37  -30.58
3     51    70.6  0.349  17.78  382.79

by entry time:
            trades win_pct  avg_r  sum_r pnl_adj
09:50-10:30     11    63.6  0.118   1.29   53.33
10:30-11:30     68    63.2  0.091   6.21  197.68
11:30-13:00     63    57.1  0.172  10.81    76.7
13:00-14:30      8    50.0  -0.11  -0.88   -5.94
14:30-15:00      1   100.0   0.75   0.75    13.3

symbol-days with >= 2 lots: 38 of 62, R +22.64, $+358.55
                   lots     R     pnl
date       symbol                    
2026-10-22 JBS        3 -3.96  -68.16
2026-10-21 FTNT       3 -3.23  -58.10
2026-10-15 CRCL       3 -3.08  -36.92
2026-10-20 OUST       3 -2.63  -54.87
2026-10-21 TKNO       2 -2.52 -118.83
2026-10-15 BULL       2 -2.30  -46.02
           USAR       2 -2.18  -29.94
2026-10-20 NBIS       3 -1.09  -25.46
           AXTI       3 -0.86  -25.28
2026-10-14 AVEX       4 -0.67   -6.23
2026-10-20 CIFR       3 -0.65  -19.61
           QNT        3 -0.61  -14.68
2026-10-22 IBX        2 -0.11  -10.63
           LI         3  0.07    1.63
2026-10-20 FLNC       3  0.28    6.94
           NVTS       3  0.38    9.39
2026-10-16 FMC        6  0.38   -0.15
2026-10-20 SMR        3  0.47    9.81
           COHR       3  0.48    8.44
2026-10-19 SOXS       5  0.54   13.59
2026-10-20 OKLO       3  0.65   11.55
           HPE        3  0.81   12.49
2026-10-22 FMC        3  0.83   51.58
2026-10-20 SOXL       3  1.28   35.93
           AAOI       3  1.34   37.40
2026-10-22 SNAP       7  1.85   10.46
2026-10-16 TLK        2  2.02   10.59
2026-10-20 RIOT       3  2.15   48.77
2026-10-19 TLK        2  2.39   20.01
2026-10-20 PENG       3  2.67   68.85
           RCUS       3  2.89   31.12
           CRWV       3  2.94   55.36
           INFQ       4  3.08   54.27
           ALM        5  3.39   72.71
           WULF       5  3.41   73.67
           APLD       4  3.43   67.34
           CORZ       4  4.32   68.39
           CLSK       5  4.47   93.14

## Session labels (regime1022 rules)
             o2c  range  med20  regime
date                                  
2026-10-06  0.13   0.47   0.73   Quiet
2026-10-07  0.18   0.71   0.73   Quiet
2026-10-08 -0.13   0.86   0.73  Choppy
2026-10-09  0.30   0.55   0.74   Quiet
2026-10-12 -0.09   0.30   0.74   Quiet
2026-10-13  0.09   0.36   0.73   Quiet
2026-10-14 -0.69   1.24   0.73    Bear
2026-10-15  0.72   1.10   0.73    Bull
2026-10-16 -1.29   1.63   0.75    Bear
2026-10-19 -0.09   0.60   0.77   Quiet
2026-10-20  0.41   1.05   0.75  Choppy
2026-10-21  0.25   0.78   0.77  Choppy
2026-10-22 -0.31   0.85   0.77  Choppy
