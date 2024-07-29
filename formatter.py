import csv
import subprocess
from pathlib import Path


class PythonFileTester:
    def __init__(self, file_path, result_csv):
        self.file_path = Path(file_path)
        self.result_csv = Path(result_csv)

    def check_pep8_compliance(self):
        try:
            result = subprocess.run(
                ["pycodestyle", str(self.file_path)], capture_output=True, text=True
            )
            if result.returncode == 0:
                pep8_result = "PEP8チェックに合格しました。"
            else:
                pep8_result = "PEP8チェックに失敗しました。"
                pep8_result += "\n" + result.stdout
            return pep8_result
        except FileNotFoundError:
            return "pycodestyleが見つかりません。インストールされているか確認してください。"

    def run_file(self):
        try:
            result = subprocess.run(
                ["python", str(self.file_path)], capture_output=True, text=True
            )
            if result.returncode == 0:
                run_result = "スクリプトは正常に実行されました。"
            else:
                run_result = "スクリプトの実行中にエラーが発生しました。"
                run_result += "\n" + result.stderr
            return run_result
        except FileNotFoundError:
            return (
                "指定されたファイルが見つかりません。ファイルパスを確認してください。"
            )

    def write_results_to_csv(self, pep8_result, run_result):
        with open(self.result_csv, mode="a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([self.file_path.name, pep8_result, run_result])


# 使用例
file_tester = PythonFileTester("/path/to/your_script.py", "results.csv")

pep8_result = file_tester.check_pep8_compliance()
run_result = file_tester.run_file()
file_tester.write_results_to_csv(pep8_result, run_result)

print("結果がresults.csvに書き込まれました。")
