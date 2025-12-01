import os
import json

def extract_base_answers(folder_path, target_key):
    base_ans_list = []

    for file in os.listdir(folder_path):
        ignore_word = "-config.json"
        if ignore_word not in file:
            filepath = os.path.join(folder_path, file)
            try:
                print(filepath)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.loads(file)
                    print(data)
                    if target_key in data:
                        base_ans_list.append(data[target_key])
                    

            except json.JSONDecodeError:
                print(f"Error decoding JSON in file: {file}")
            
            except FileNotFoundError:
                print(f"File not found: {file}")

            except Exception as e:
                print(f"An unexpected error occured with the file {file}: {e}")

    with open("data/CounterintuitiveQA/outputs_haiku/base_ans.txt", 'w') as f:
        for item in base_ans_list:
            f.write(item + '\n')

folder_path = "data/CounterintuitiveQA/outputs_haiku"
target_key = "base_answer"
extract_base_answers(folder_path, target_key)