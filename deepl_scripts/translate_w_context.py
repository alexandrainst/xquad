import copy
import json
from pathlib import Path
import re
import os
from typing import Optional

from deepl.translator import Translator
import xmltodict
import dicttoxml
from xml.parsers.expat import ExpatError
from greynir_client.client import translate_en_to_is
import unidecode


class DummyTranslator:
    def __init__(self):
        self.character_count = 0
    def translate_text(self, text, source_lang: Optional[str]=None, target_lang: Optional[str]=None):
        self.character_count += len(text)
        return text

# "Manually" try to fix xml errors that shows up in the translation
def fix_xml_error(xml:str):
    # Fix a missing semicolon after &quot
    new_xml, count = re.subn(r"(quot)([^;])", r"\g<1>;\g<2>", xml)
    new_xml = new_xml.replace('<? xml version="1.0" encoding="UTF-8"? >', '<?xml version="1.0" encoding="UTF-8" ?>')
    print("Fixed xml error")
    print("Old: %s" % xml)
    print("New: %s" % new_xml)
    return new_xml

def translate_xquad_json(xquad_json: dict, target_lang: str, dryrun: bool=False):
    with open("deepl_key.txt", "r") as key_file:
        auth_key = key_file.read().strip()

    if dryrun:
        translator = DummyTranslator()
        translate_text = lambda x: translator.translate_text(x)
    else:
        if target_lang == "is":
            with open("greynir_apikey.txt", "r") as f:
                greynir_key = f.read().strip()
                translate_text = lambda x: translate_en_to_is(greynir_key, [unidecode.unidecode(x)]).translations[0]["translatedText"]
        else:
            translator = Translator(auth_key)
            translate_text = lambda x: translator.translate_text(x, source_lang="en", target_lang=target_lang, tag_handling="xml", preserve_formatting=True).text

    xquad_translated = copy.deepcopy(xquad_json)

    # Loop through the json and translate
    for topic_idx, topic in enumerate(xquad_json["data"]):
        print(topic["title"], len(topic["paragraphs"]))
        xquad_translated["data"][topic_idx]["title"] = translate_text(topic["title"])
        for paragraph_idx, paragraph in enumerate(topic["paragraphs"]):

            # Convert paragraph and questions into a more compact format for xml
            context = paragraph["context"]

            qa_list = []
            for qa in paragraph["qas"]:
                question = qa["question"]
                assert len(qa["answers"]) == 1
                for answer in qa["answers"]:
                    qa_list.append({"q": question, "a": answer["text"]})

            to_translate = {"context": context, "qas": qa_list}

            # Translate object to xml
            xml = dicttoxml.dicttoxml(to_translate, root=True, attr_type=False, return_bytes=False)
            restored = xmltodict.parse(xml)
            translated = translate_text(xml)
            try:
                translated_dict = xmltodict.parse(translated)["root"]
            except ExpatError:
                fixed_xml = fix_xml_error(translated)
                translated_dict = xmltodict.parse(fixed_xml)["root"]

            # Put translated text back into original structure
            xquad_translated["data"][topic_idx]["paragraphs"][paragraph_idx]["context"] = translated_dict["context"]
            if len(paragraph["qas"]) == 1:
                # If there is only one question the xml is not parsed as a list
                xquad_translated["data"][topic_idx]["paragraphs"][paragraph_idx]["qas"][0]["question"] = translated_dict["qas"]["item"]["q"]
                for ans_idx, answer in enumerate(qa["answers"]):
                    xquad_translated["data"][topic_idx]["paragraphs"][paragraph_idx]["qas"][0]["answers"][ans_idx]["text"] = translated_dict["qas"]["item"]["a"]
            else:
                for qa_idx, qa in enumerate(paragraph["qas"]):
                    xquad_translated["data"][topic_idx]["paragraphs"][paragraph_idx]["qas"][qa_idx]["question"] = translated_dict["qas"]["item"][qa_idx]["q"]
                    for ans_idx, answer in enumerate(qa["answers"]):
                        xquad_translated["data"][topic_idx]["paragraphs"][paragraph_idx]["qas"][qa_idx]["answers"][ans_idx]["text"] = translated_dict["qas"]["item"][qa_idx]["a"]

    return xquad_translated


def main():
    #target_langs = ["da", "sv", "nb", "nl"] #, "is"]
    #target_langs = ["da",] #, "is"]
    target_langs = ["is"]

    input_json_file_path = Path("../xquad.en.json")


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
