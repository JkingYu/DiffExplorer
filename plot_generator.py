import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf

BLUE_COLORS = ['#345699','#3F66B4','#4874CB','#90A3D8','#BBC4E5','#C1C9E7']

def get_colors(n):
    colors = BLUE_COLORS
    return (colors * ((n // len(colors)) + 1))[:n]

def plot_indicator(ind, long_data, res, scheme, outdir, group_order):
    unique_groups = long_data[long_data['Indicator']==ind]['Group'].unique()
    groups = [g for g in group_order if g in unique_groups]
    for g in unique_groups:
        if g not in groups:
            groups.append(g)

    means = []
    stds = []
    for g in groups:
        vals = long_data[(long_data['Indicator']==ind) & (long_data['Group']==g)]['Value']
        means.append(vals.mean())
        stds.append(vals.std(ddof=0) if len(vals) > 1 else 0)
    x = np.arange(len(groups))

    width_inch = 96.52 / 25.4
    height_inch = 101.6 / 25.4
    fig, ax = plt.subplots(figsize=(width_inch, height_inch))
    ax.bar(x, means, yerr=stds, capsize=3, width=0.4,
           color=get_colors(len(groups)), edgecolor='none')
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontname='Times New Roman', fontsize=9)
    ax.set_ylabel('Value', fontname='Times New Roman', fontsize=10)
    ax.set_title(ind, fontname='Times New Roman', fontsize=11, weight='bold')

    post = res[(res['Indicator'] == ind) & (res['Comparison'] != 'Overall')]
    if not post.empty:
        if 'P_Adjusted' in post.columns and not post['P_Adjusted'].isna().all():
            p_col = 'P_Adjusted'
        elif 'P_Value' in post.columns:
            p_col = 'P_Value'
        else:
            p_col = None
        if p_col is not None:
            pairs = []
            for _, row in post.iterrows():
                comp = row['Comparison']
                p = row[p_col]
                if pd.isna(p):
                    continue
                parts = comp.split(' vs ')
                if len(parts) == 2:
                    g1, g2 = parts[0].strip(), parts[1].strip()
                    if g1 in groups and g2 in groups:
                        pairs.append((groups.index(g1), groups.index(g2), p))
            if pairs:
                ymax = max([m + s for m, s in zip(means, stds)]) * 1.1
                for i, (i1, i2, p) in enumerate(sorted(pairs, key=lambda x: x[2])):
                    y = ymax + i * 0.08 * ymax
                    ax.plot([i1, i2], [y, y], 'k', lw=0.6)
                    if p < 0.001:
                        stars = '***'
                    elif p < 0.01:
                        stars = '**'
                    elif p < 0.05:
                        stars = '*'
                    else:
                        stars = 'ns'
                    ax.text((i1+i2)/2, y*1.002, stars, ha='center', va='bottom',
                            fontsize=8, fontname='Times New Roman')
    ax.spines[['top','right']].set_visible(False)
    os.makedirs(outdir, exist_ok=True)
    base = ind.replace(' ', '_').replace('/', '_')
    plt.tight_layout()
    plt.savefig(f'{outdir}/{base}.png', dpi=500, facecolor='none')
    plt.savefig(f'{outdir}/{base}.pdf', format='pdf', transparent=True, facecolor='none')
    plt.close()
    return f'{outdir}/{base}.png', f'{outdir}/{base}.pdf'

def prepare_data(data_path, result_path):
    raw = pd.read_excel(data_path, header=None)
    group_names = raw.iloc[0,1:].astype(str).str.strip().tolist()
    samples = raw.iloc[1,1:].astype(str).str.strip().tolist()
    indicators = raw.iloc[2:,0].astype(str).str.strip().tolist()
    mat = raw.iloc[2:,1:].values
    records = []
    for i, ind in enumerate(indicators):
        for j, (g, s) in enumerate(zip(group_names, samples)):
            if pd.notna(mat[i,j]):
                records.append({'Indicator': ind, 'Group': g, 'Value': float(mat[i,j])})
    long_data = pd.DataFrame(records)
    res_df = pd.read_excel(result_path, sheet_name='Results')
    group_order = []
    for g in group_names:
        if g not in group_order:
            group_order.append(g)
    return long_data, res_df, group_order, indicators