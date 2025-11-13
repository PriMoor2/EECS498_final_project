import json

with open("CIAR.json", 'r', encoding="utf-8") as f:
    data = json.load(f)

values = []
for item in data:
    if "question" in item:
        values.append(item["question"])

with open("input.txt", 'w', encoding="utf-8") as f:
    for value in values:
        f.write(value + "\n")
