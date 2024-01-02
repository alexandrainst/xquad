import re
import math
import copy
import json
from pathlib import Path
import sys

def realign_answer_positions(xquad_json: dict, xquad_json_orig: dict):
    xquad_aligned = copy.deepcopy(xquad_json)
    for topic_idx, topic in enumerate(xquad_json["data"]):
        for paragraph_idx, paragraph in enumerate(topic["paragraphs"]):
            context = paragraph["context"]
            for qa_idx, qa in enumerate(paragraph["qas"]):
                question = qa["question"]
                for ans_idx, answer in enumerate(qa["answers"]):
                    answer_text = answer["text"]
                    answer_start = answer["answer_start"]
                    matches = list(re.finditer(re.escape(answer_text.lower()), context.lower()))
                    start_int = -1
                    if len(matches) > 1:
                        # Find the starting position in the original (non-translated) text as a percentage of the text.
                        orig_start_percentage = xquad_json_orig["data"][topic_idx]["paragraphs"][paragraph_idx]["qas"][qa_idx]["answers"][ans_idx]["answer_start"]/len(xquad_json_orig["data"][topic_idx]["paragraphs"][paragraph_idx]["context"])
                        # Find the closest matching starting position (in percentage) in the new text.
                        best_error = math.inf
                        for m in matches:
                            start_percentage = m.start()/len(context)
                            current_error = abs(start_percentage-orig_start_percentage)
                            if current_error < best_error:
                                best_error = current_error
                                start_int = m.start()
                    elif len(matches) == 0:
                        print(context)
                        print(question)
                        print(answer_text)
                        # Reasign variables in case they were changed in breakpoint
                        xquad_aligned["data"][topic_idx]["paragraphs"][paragraph_idx]["qas"][qa_idx]["answers"][ans_idx]["answer_start"] = start_int
                        xquad_aligned["data"][topic_idx]["paragraphs"][paragraph_idx]["qas"][qa_idx]["answers"][ans_idx]["text"] = answer_text
                        xquad_aligned["data"][topic_idx]["paragraphs"][paragraph_idx]["qas"][qa_idx]["question"] = question
                        xquad_aligned["data"][topic_idx]["paragraphs"][paragraph_idx]["context"] = context
                    else:
                        start_int = matches[0].start()
                    xquad_aligned["data"][topic_idx]["paragraphs"][paragraph_idx]["qas"][qa_idx]["answers"][ans_idx]["answer_start"] = start_int

    return xquad_aligned

def main():
    input_json_file_path = Path(sys.argv[1])
    orig_input_json_file_path = Path(sys.argv[2])

    with open(input_json_file_path, "r") as input_json_file:
        loaded_json = json.load(input_json_file)

    with open(orig_input_json_file_path, "r") as orig_input_json_file:
        orig_json = json.load(orig_input_json_file)

    aligned = realign_answer_positions(loaded_json, orig_json)
    with open("fixed_" + input_json_file_path.name, "w") as outfile:
        json.dump(aligned, outfile, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
