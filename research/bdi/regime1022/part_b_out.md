# Part B - protection rules (2-year backtest books; costs in)

## primary

                             variant  train_total_R  valid_total_R  train_kept_pct  valid_kept_pct  train_vs_random_thin_R  valid_vs_random_thin_R  all_worst_day  all_worst5pct_mean  all_parent_worst5pct_days_mean  all_days_le_m10
                           P0 as-run        -2633.3        -1052.2           100.0           100.0                     0.0                     0.0         -150.6              -88.22                          -88.22              203
 B1a per-setup 1 open lot per symbol        -2228.6         -953.7            83.9            84.6                   -19.9                   -63.9          -96.5              -68.24                          -64.14              190
B1b per-setup 2 open lots per symbol        -2569.4        -1020.4            95.5            95.2                   -54.1                   -18.9         -118.1              -82.07                          -80.52              201
       B1c per-setup max 5 open lots        -1474.9         -541.3            60.6            54.3                   120.8                    30.5          -39.1              -31.77                          -19.26              147
      B1d per-setup max 10 open lots        -1855.8         -658.9            78.3            72.5                   206.2                   104.2          -58.8              -43.16                          -31.11              186
B2a per-setup realized+open stop -3R         -959.3         -358.7            43.5            38.2                   187.4                    43.6          -28.5              -21.75                          -12.01              120
B2b per-setup realized+open stop -4R        -1214.7         -469.1            50.9            45.7                   125.2                    12.1          -31.8              -26.21                          -14.96              152
 B3a account realized+open stop -10R         -718.1         -287.4            31.5            26.0                   110.3                   -13.4          -23.4              -13.02                           -9.67               61
 B3b account realized+open stop -15R         -982.9         -313.7            43.4            36.4                   159.7                    69.8          -35.2              -18.39                          -13.72              141
 B3c account realized+open stop -20R        -1210.3         -402.6            53.1            44.9                   187.2                    70.0          -49.8              -23.47                          -17.83              170
  B4a cluster cap 3 (20d corr > 0.7)        -2106.7         -962.4            82.9            83.7                    76.6                   -81.2          -96.8              -61.13                          -52.30              185
  B4b cluster cap 5 (20d corr > 0.7)        -2233.0         -987.1            87.8            90.0                    78.7                   -40.5          -94.4              -66.52                          -58.92              194

## testing

                             variant  train_total_R  valid_total_R  train_kept_pct  valid_kept_pct  train_vs_random_thin_R  valid_vs_random_thin_R  all_worst_day  all_worst5pct_mean  all_parent_worst5pct_days_mean  all_days_le_m10
                           P0 as-run        -3523.4        -1390.8           100.0           100.0                     0.0                     0.0         -205.2             -114.31                         -114.31              213
 B1a per-setup 1 open lot per symbol        -3478.3        -1341.9            96.9            95.8                   -63.2                    -9.8         -191.7             -110.23                         -110.19              209
B1b per-setup 2 open lots per symbol        -3521.8        -1379.6            99.5            99.3                   -15.4                     0.9         -203.1             -113.59                         -113.59              212
       B1c per-setup max 5 open lots        -1557.3         -563.0            48.0            44.6                   135.2                    57.7          -43.9              -32.68                          -23.66              161
      B1d per-setup max 10 open lots        -2177.3         -697.3            67.3            63.4                   193.5                   183.9          -67.6              -49.58                          -39.01              188
B2a per-setup realized+open stop -3R        -1202.6         -345.1            37.4            35.1                   114.7                   142.7          -28.7              -24.19                          -16.26              144
B2b per-setup realized+open stop -4R        -1521.8         -431.2            44.0            41.5                    27.4                   145.9          -38.0              -29.23                          -21.65              170
 B3a account realized+open stop -10R         -750.0         -284.7            20.2            16.2                   -37.0                   -59.2          -13.5              -12.27                           -8.25               64
 B3b account realized+open stop -15R        -1088.5         -396.0            28.3            23.2                   -90.6                   -73.7          -19.8              -17.12                          -12.25              142
 B3c account realized+open stop -20R        -1449.6         -400.6            36.2            29.8                  -173.8                    14.3          -24.1              -22.03                          -16.62              172
  B4a cluster cap 3 (20d corr > 0.7)        -2676.0        -1203.0            80.4            81.0                   155.2                   -77.2         -137.6              -80.72                          -70.81              201
  B4b cluster cap 5 (20d corr > 0.7)        -2849.6        -1257.7            85.9            87.4                   177.6                   -41.9         -156.9              -87.51                          -80.87              211

## testing2

                             variant  train_total_R  valid_total_R  train_kept_pct  valid_kept_pct  train_vs_random_thin_R  valid_vs_random_thin_R  all_worst_day  all_worst5pct_mean  all_parent_worst5pct_days_mean  all_days_le_m10
                           P0 as-run        -1920.7         -430.6           100.0           100.0                     0.0                     0.0         -125.5              -71.82                          -71.82              183
 B1a per-setup 1 open lot per symbol        -1886.6         -467.6            96.1            95.1                   -41.2                   -58.1         -128.3              -70.04                          -69.92              182
B1b per-setup 2 open lots per symbol        -1913.6         -460.8            99.2            99.0                    -8.1                   -34.3         -124.4              -71.79                          -71.77              184
       B1c per-setup max 5 open lots        -1088.9         -269.9            55.8            50.3                   -17.2                   -53.2          -43.0              -29.54                          -24.51              127
      B1d per-setup max 10 open lots        -1467.6         -280.0            76.4            70.8                    -0.7                    24.7          -62.8              -42.34                          -39.31              157
B2a per-setup realized+open stop -3R         -939.4         -206.2            43.1            39.2                  -110.7                   -37.6          -30.6              -21.99                          -17.86               97
B2b per-setup realized+open stop -4R        -1123.6         -227.4            50.9            46.5                  -146.8                   -27.3          -39.8              -25.38                          -21.81              128
 B3a account realized+open stop -10R         -699.4         -156.7            29.1            25.0                  -140.8                   -49.1          -15.8              -12.23                           -8.63               53
 B3b account realized+open stop -15R        -1001.8         -231.7            40.8            34.5                  -217.7                   -83.4          -22.5              -17.55                          -13.77              127
 B3c account realized+open stop -20R        -1226.8         -289.9            50.8            43.7                  -250.5                  -101.6          -27.2              -22.80                          -18.68              158
  B4a cluster cap 3 (20d corr > 0.7)        -1695.5         -559.9            83.7            84.7                   -88.3                  -195.1          -93.7              -54.86                          -50.76              170
  B4b cluster cap 5 (20d corr > 0.7)        -1755.9         -530.6            88.3            90.9                   -60.8                  -139.3         -104.6              -59.54                          -55.97              174

## graveyard

                             variant  train_total_R  valid_total_R  train_kept_pct  valid_kept_pct  train_vs_random_thin_R  valid_vs_random_thin_R  all_worst_day  all_worst5pct_mean  all_parent_worst5pct_days_mean  all_days_le_m10
                           P0 as-run        -1624.2        -1102.9           100.0           100.0                     0.0                     0.0          -98.9              -50.16                          -50.16              165
 B1a per-setup 1 open lot per symbol        -1599.1        -1087.6            99.3            99.0                    13.5                     4.8          -98.9              -49.16                          -49.02              161
B1b per-setup 2 open lots per symbol        -1624.2        -1103.8           100.0           100.0                     0.0                    -1.0          -98.9              -50.16                          -50.16              165
       B1c per-setup max 5 open lots         -956.6         -657.6            62.0            53.0                    50.4                   -72.6          -26.2              -22.32                          -17.45              103
      B1d per-setup max 10 open lots        -1274.3         -850.4            82.3            76.3                    62.3                    -8.9          -46.1              -32.01                          -29.74              146
B2a per-setup realized+open stop -3R         -789.5         -472.5            48.6            41.3                    -0.2                   -17.1          -19.3              -16.34                          -11.67               61
B2b per-setup realized+open stop -4R         -876.2         -569.7            56.7            49.5                    45.4                   -24.2          -22.7              -19.19                          -14.41               84
 B3a account realized+open stop -10R         -650.5         -440.2            45.5            33.2                    89.0                   -73.9          -11.9              -11.05                           -8.60               38
 B3b account realized+open stop -15R         -985.6         -560.8            60.3            46.9                    -5.6                   -43.4          -16.7              -15.49                          -12.60              110
 B3c account realized+open stop -20R        -1184.1         -647.5            71.9            58.7                   -17.1                    -0.4          -21.8              -20.37                          -16.44              153
  B4a cluster cap 3 (20d corr > 0.7)        -1397.8        -1036.5            89.2            90.5                    51.3                   -37.8          -61.8              -37.52                          -34.04              151
  B4b cluster cap 5 (20d corr > 0.7)        -1478.9        -1092.9            92.9            95.1                    29.8                   -43.5          -72.0              -41.32                          -39.13              159
