import pandas as pd
import os
import re

def smart_load(file_path, output_dir="temp"):
    os.makedirs(output_dir, exist_ok=True)
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.xls', '.xlsx']:
        df = pd.read_excel(file_path, header=None, dtype=str)
    elif ext == '.csv':
        df = pd.read_csv(file_path, header=None, dtype=str, encoding='utf-8-sig')
    elif ext == '.txt':
        try:
            df = pd.read_csv(file_path, header=None, dtype=str, sep='\t', encoding='utf-8-sig')
        except:
            df = pd.read_csv(file_path, header=None, dtype=str, sep=',', encoding='utf-8-sig')
    else:
        raise ValueError("Unsupported file format")
    df = df.dropna(how='all').dropna(axis=1, how='all')
    if df.shape[0] < 3 or df.shape[1] < 3:
        raise ValueError("Data too small")

    first = str(df.iloc[0, 0]).strip().lower()
    second = str(df.iloc[1, 0]).strip().lower()
    third = str(df.iloc[2, 0]).strip().lower()
    is_target = (re.search(r'group', first) and re.search(r'sample', second) and
                 not re.search(r'group|sample', third))

    if is_target:
        out = df.copy()
    else:
        # 判断第一行是否为列名（含group或sample或非数字）
        first_cell = str(df.iloc[0, 0]).strip()
        try:
            float(first_cell)
            has_header = False
        except:
            has_header = True
        if has_header:
            groups = df.iloc[1:, 0].astype(str).str.strip().tolist()
            samples = df.iloc[1:, 1].astype(str).str.strip().tolist()
            var_names = df.iloc[0, 2:].astype(str).str.strip().tolist()
            mat = df.iloc[1:, 2:].apply(pd.to_numeric, errors='coerce').values.T
        else:
            groups = df.iloc[:, 0].astype(str).str.strip().tolist()
            samples = df.iloc[:, 1].astype(str).str.strip().tolist()
            var_names = [f"Var{i+1}" for i in range(df.shape[1]-2)]
            mat = df.iloc[:, 2:].apply(pd.to_numeric, errors='coerce').values.T

        table = [['Groups'] + groups, ['Samples'] + samples]
        for i, v in enumerate(var_names):
            table.append([v] + mat[i, :].tolist())
        out = pd.DataFrame(table)

    out_path = os.path.join(output_dir, 'input_R_data.xlsx')
    out.to_excel(out_path, index=False, header=False, engine='openpyxl')
    return out_path

if __name__ == "__main__":
    test = r"E:\Zaa_宏基因-mapping\DiffExplorer_Project\try1.xlsx"
    if os.path.exists(test):
        print(smart_load(test))