import plotly.offline as py
import plotly.graph_objs as go
import pickle

with open("C:/WORK/science/onpositive_data/python/texts/sule1.txt-surface.pcl", 'rb') as f:
    allData = pickle.load(f)

data = []
size = None
PARAM = "UNIQUE_ADJS"
for dEl in allData[PARAM]:
    max_value = max(allData[PARAM][dEl])
    min_value = min(allData[PARAM][dEl])
    allData[PARAM][dEl] = [(x-min_value)/(max_value-min_value) for x in allData[PARAM][dEl]] 
    if not size:
        size = len(allData[PARAM][dEl])
    else:
        while len(allData[PARAM][dEl]) != size:
            allData[PARAM][dEl].append(0)
    data.append(allData[PARAM][dEl])

trace = go.Heatmap(z=data,
                   y=list(allData["DOTS"].keys()))
picture=[trace]
print(py.plot(picture, filename='labelled-heatmap.html'))