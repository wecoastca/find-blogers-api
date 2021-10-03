from io import BytesIO
import pandas as pd

def df_to_excel(df, filename):
    df_copy = df.copy()
    
    bio = BytesIO()
    writer = pd.ExcelWriter(bio, engine="xlsxwriter")
    df_copy.to_excel(writer,filename)

    writer.save()
    bio.seek(0)
    return bio