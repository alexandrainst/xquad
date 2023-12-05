import copy
import json
from pathlib import Path
import os
from typing import Optional

from deepl.translator import Translator


class DummyTranslator:
    def __init__(self):
        self.character_count = 0
    def translate_text(self, text, source_lang: Optional[str]=None, target_lang: Optional[str]=None):
        self.character_count += len(text)
        return text

def translate_xquad_json(xquad_json: dict, target_lang: str, dryrun: bool=False):
    with open("deepl_key.txt", "r") as key_file:
        auth_key = key_file.read().strip()

    if dryrun:
        translator = DummyTranslator()
    else:
        translator = Translator(auth_key)

    xquad_translated = copy.deepcopy(xquad_json)

    translate = lambda x: translator.translate_text(x, source_lang="en", target_lang=target_lang).text

    total_text_len = 0
    # Loop through the json and translate
    for topic_idx, topic in enumerate(xquad_json["data"]):
        topic_text_len = 0
        print(topic["title"], len(topic["paragraphs"]))
        xquad_translated["data"][topic_idx]["title"] = translate(topic["title"])
        for paragraph_idx, paragraph in enumerate(topic["paragraphs"]):
            context = paragraph["context"]
            topic_text_len += len(context)
            xquad_translated["data"][topic_idx]["paragraphs"][paragraph_idx]["context"] = translate(context)
            for qa_idx, qa in enumerate(paragraph["qas"]):
                question = qa["question"]
                topic_text_len += len(question)
                xquad_translated["data"][topic_idx]["paragraphs"][paragraph_idx]["qas"][qa_idx]["question"] = translate(question)
                for ans_idx, answer in enumerate(qa["answers"]):
                    answer_text = answer["text"]
                    topic_text_len += len(answer["text"])
                    answer_start = answer["answer_start"]
                    cut_answer = context[answer_start:answer_start+len(answer_text)]
                    assert cut_answer == answer_text
                    xquad_translated["data"][topic_idx]["paragraphs"][paragraph_idx]["qas"][qa_idx]["answers"][ans_idx]["text"] = translate(answer_text)
        total_text_len += topic_text_len
        print(topic["title"], topic_text_len)

    print(total_text_len)

    return xquad_translated


def main():
    #target_langs = ["da", "se", "no", "nl"] #, "is"]
    target_langs = ["da",] #, "is"]

    input_json_file_path = Path("../xquad.mini.en.json")


    with open(input_json_file_path, "r") as input_json_file:
        xquad_en = json.load(input_json_file)

    for lang in target_langs:
        xquad_translated = translate_xquad_json(xquad_en, lang, dryrun=False)
        outname = input_json_file_path.name.replace(".en.", f".{lang}.")
        print("outname:", outname)
        with open(outname, "w") as outfile:
            json.dump(xquad_translated, outfile, indent=2)

if __name__ == "__main__":
    main()
