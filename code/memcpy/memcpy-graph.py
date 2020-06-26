import pandas as pd
import plotly.graph_objs as go
import plotly
import sys

file_name = sys.argv[1]


def replace_multiple(string, delimiters):
  for delimiter in delimiters:
      string = string.replace(delimiter, '.')
  parts = string.split('.')
  return list(filter(lambda s: s != '', parts))


df = pd.read_csv(file_name)
df = df[['name', 'bytes_per_second']]

new_df = pd.DataFrame(columns=['method', 'size', 'mean', 'median', 'stddev'])
for i in range(0, len(df), 3):
  fn = lambda j: df.iloc[j]["bytes_per_second"]
  mean = fn(i)
  median = fn(i+1)
  stddev = fn(i+2)
  name = df.iloc[i]["name"]
  parts = replace_multiple(name, ['::', '<', '>', '/', '_'])
  if parts[3] == 'dragons':
    method = parts[4]
    size = parts[5]
  else:
    method = parts[3]
    size = parts[4]

  new_df = new_df.append({
    "method": method,
    "mean": mean,
    "median": median,
    "stddev": stddev,
    "size": size,
  }, ignore_index=True)

data_sizes = map(int, new_df["size"].to_list())
data_sizes = sorted(set(data_sizes))
methods = new_df["method"].unique()

def convert_to_byte_str(intval):
  if intval < 1024:
    return str(intval) + 'B'
  elif intval < 1024 * 1024:
    return str(intval / 1024) + 'kB'
  elif intval < 1024 * 1024 * 1024:
    return str(intval / (1024 * 1024)) + 'MB'

def convert_to_gbps(bytes_per_second):
  return bytes_per_second / (1024 ** 3)

data_list = []
for method in methods:
  method_rows = new_df.loc[new_df['method'] == method]
  mean_ys = []
  median_ys = []
  stddev_ys = []
  for data_size in data_sizes:
    data_size_row = method_rows.loc[method_rows["size"] == str(data_size)]
    mean_ys.append(data_size_row["mean"].to_list()[0])
    median_ys.append(data_size_row["median"].to_list()[0])
    stddev_ys.append(data_size_row["stddev"].to_list()[0])

  str_data_list = list(map(convert_to_byte_str, data_sizes))
  bar = go.Bar(
    name=method, 
    x=str_data_list, 
    y=list(map(convert_to_gbps, mean_ys)),
    error_y=dict(type='data', array=list(map(convert_to_gbps, stddev_ys)))
  )
  data_list.append(bar)

fig = go.Figure(data = data_list)
fig.update_layout(barmode='group',
  yaxis=dict(
    title_text='Speed',
    ticksuffix='GB/s'
  ),
  xaxis=dict(
    title_text='Data sizes'
  )
)

print(plotly.offline.plot(fig, include_plotlyjs=False, output_type='div'))
