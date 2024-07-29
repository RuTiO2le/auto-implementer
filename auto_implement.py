import datetime
import json
import os
import pathlib

import fitz  # PyMuPDF
import yaml
from openai import OpenAI
import pandas as pd

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def read_pdf(file_path):
    document = fitz.open(file_path)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    return text


def extract_method(text):
    # キーワード検索
    start_idx = text.lower().find("method")
    end_idx = text.lower().find("results")
    if start_idx != -1 and end_idx != -1:
        method_section = text[start_idx:end_idx]
    else:
        method_section = "Method section not found"
    return method_section


def extract_method_by_llm(text):
    system_prompt = "あなたは優秀な研究者です"
    prompt = f"""
    以下の論文から、バンド選択の手法に関する部分を過不足なく抽出してください。
    
    論文:
    {text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        # max_tokens=1500
    )

    method_section = response.choices[0].message.content.strip()
    return (method_section, response.usage)


def write_to_file(pdf_file_path, class_def, method_description, file_dir):
    system_prompt = """
    あなたは優秀な研究者でプログラミングにも長けています。
    回答は全てJSON形式で回答してください。
    """

    assistant_prompt = (
        '{"program": "", "name_of_method": "", "explanation_of_method_in_Japanese": ""}'
    )

    prompt = f"""
    以下の仮想クラスを継承して、バンド選択の手法を実装してください(仮想クラスの出力は不要)。
    また、PCAのような形式で手法名を出力し、その手法の説明を記述してください。

    仮想クラス:
    {class_def}
    バンド選択の手法:
    {method_description}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": assistant_prompt},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
        # max_tokens=1500
    )

    res = json.loads(response.choices[0].message.content)
    class_code = res["program"]
    method_name = res["name_of_method"]
    method_explanation = res["explanation_of_method_in_Japanese"]

    now = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    method_explanation = (
        f"{pdf_file_path}を実装\n\n"
        + method_explanation
        + f"\n\nGPT-4により{now}に実行"
    )

    with open(os.path.join(file_dir, f"gpt_{method_name}.py"), "w") as file:
        file.write(class_code)
    with open(os.path.join(file_dir, f"{method_name}.txt"), "w") as file:
        file.write(method_explanation)

    return (response.usage, method_name)


def update_yaml(file_path, pdf_file_path, method_name, cost):
    data = {}
    data[pdf_file_path] = {"method_name": method_name, "cost": cost}

    with open(file_path, "a") as yaml_file:
        yaml.safe_dump(data, yaml_file, default_flow_style=False)


def update_json(pdf_file_path, method_name, cost):
    data = {
        "file_name": os.path.basename(pdf_file_path),
        "content": [{"method_name": method_name, "cost": cost}],
    }

    with open("./is_done.jsonl", "a") as json_file:
        json.dump(data, json_file, indent=4)


def main(pdf_file_path, output_file_dir, class_def, yaml_file_path):
    if not os.path.exists("is_done.jsonl"):
        pathlib.Path("is_done.jsonl").touch()
    with open('is_done.jsonl', 'r') as f:
        s = f.read()
    if os.path.basename(pdf_file_path) in s:
        print(f"{os.path.basename(pdf_file_path)} is already done.")
        return
    else:
        print(f"Processing {os.path.basename(pdf_file_path)}")

    pdf_text = read_pdf(pdf_file_path)
    method_section, tokens1 = extract_method_by_llm(pdf_text)
    cost = tokens1.completion_tokens * 0.0000006 + tokens1.prompt_tokens * 0.00000015
    tokens2, method_name = write_to_file(
        pdf_file_path, class_def, method_section, output_file_dir
    )
    cost += tokens2.completion_tokens * 0.000015 + tokens2.prompt_tokens * 0.000005
    update_yaml(yaml_file_path, pdf_file_path, method_name, cost)
    update_json(pdf_file_path, method_name, cost)


if __name__ == "__main__":
    class_def = '''
class BaseFeatureExtractor(ABC):
    def __init__(self, feature_extractor):
        """
        feature_extractor: Class that transforms high dimensional HSI data to lower dimensional HSI data and has a transform method.
                        The transform method receives np.array: (B, C_high, H_before, W_before) and returns np.array: (B, C_low, H_after, W_after) where C_low < C_high.
        """
        self.feature_extractor = feature_extractor

    def __call__(self, x: np.array) -> np.array:
        return self.transform(x)

    @abstractmethod
    def transform(self, x: np.array) -> np.array:
        pass

    def fit(self, *args):
        pass
    '''

    pdf_files = os.listdir("../paper/decomposition")
    for pdf_file in pdf_files:
        pdf_file_path = f"../paper/decomposition/{pdf_file}"
        output_file_dir = (
            "../HSI-feature-extraction/hsi-feature-extraction/src/decomposition"
        )
        yaml_file_path = "./yaml_pool/decomposition.yaml"
        main(pdf_file_path, output_file_dir, class_def, yaml_file_path)

    pdf_files = os.listdir("../paper/selection")
    for pdf_file in pdf_files:
        pdf_file_path = f"../paper/selection/{pdf_file}"
        output_file_dir = (
            "../HSI-feature-extraction/hsi-feature-extraction/src/selection"
        )
        yaml_file_path = "./yaml_pool/selection.yaml"
        main(pdf_file_path, output_file_dir, class_def, yaml_file_path)
