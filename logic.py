def filtriraj(df, tekst):
    if not tekst:
        return df
    tekst = tekst.lower()
    return df[df.apply(lambda row: row.astype(str).str.lower().str.contains(tekst).any(), axis=1)]
