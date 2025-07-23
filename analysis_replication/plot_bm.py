
import re
from math import log10
import seaborn as sns
from matplotlib import pyplot as plt

# df = survey(host, study='Bone marrow aging')
df['qual'] = df['multiplier'] * df['p'].apply(log10)
prox = df[df['metric'] == 'proximity']
prox['-log10(p)'] = prox['p'].apply(log10) * -1
def map_names(c: str) -> str:
    m = {
        '1': '>60 y.o.',
        '2': '20-60 y.o.',
        '3': '<20 y.o.',
    }
    return m[c]
prox['elevated in cohort'] = prox['higher_cohort'].apply(map_names)

fig, ax = plt.subplots(1, 1, figsize=(7, 7))
sns.scatterplot(data=prox, x='multiplier', y='-log10(p)', hue='elevated in cohort', s=21, ax=ax)
ax.set_ylim((0, 4.0))
ax.set_xlim((0, 5.5))


offsets = [
    [0.05, 0.05, 0.05, 0.05, 0.05],
    [0, 0, 0.04, -0.15, -0.1],
]
count = 0
for i, row in prox.sort_values(by='qual').head(5).iterrows():
    label = re.sub('_', ' ', f'{row["p2"]} near \n{row["p1"]}')
    label = re.sub(r'\+', ' ', label)
    y = row['-log10(p)']
    ax.text(row['multiplier'] + offsets[0][count], y + offsets[1][count], label, fontsize=8)
    count += 1

for i, row in prox[(prox['qual'] > -8.0) & (prox['multiplier'] > 3.5)].sort_values(by='qual').head(5).iterrows():
    label = re.sub('_', ' ', f'{row["p2"]} near \n{row["p1"]}')
    label = re.sub(r'\+', ' ', label)
    y = row['-log10(p)']
    ax.text(row['multiplier'] + 0.05, y, label, fontsize=8)

fig.suptitle('Phenotype-to-phenotype proximity (number cells within 50um)\nt-test for age cohort difference')
fig.savefig('bm.svg')
plt.show()
