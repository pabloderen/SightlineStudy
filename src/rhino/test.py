import pandas as pd
import numpy as np

a = pd.DataFrame([1,2,3,4], columns=['a'])
b  = pd.DataFrame([1,2,3], columns=['b'])
c =a.join(b, how='left')
print(c)