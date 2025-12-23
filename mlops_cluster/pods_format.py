import sys
import pandas as pd
from io import StringIO

"""
Formats the output of kubectl get pods -A
with custom columns
"""

data = sys.stdin.read()
df = pd.read_csv(StringIO(data), sep=r'\s+')


groupby_columns = ["NAMESPACE", "NODE"]
other_columns = [column for column in df.columns if column not in groupby_columns]

grouped = df.groupby(groupby_columns)


for (namespace, node), group in grouped:
    print(f"""
#{len(namespace)*'-'}---
# {namespace}  |
#{len(namespace)*'-'}---
    └── NODE : {node}
""", end="")
    for _, row in group[other_columns].iterrows():
        # Build all "col: value" lines first
        lines = [f"-{col}: {value}" for col, value in row.items()]
        # Determine the width of the longest line
        width = max(len(line) for line in lines)
        # Borders
        top = "        +" + "-" * (width + 2) + "+"
        bottom = top
        # Print
        print(top)
        for line in lines:
            print(f"        | {line.ljust(width)} |")
        print(bottom + "\n")