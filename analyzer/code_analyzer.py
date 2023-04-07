import os
import time

from analyzer.chatgpt_service import LLMService, ChatGPTService


class CodeAnalyzerService:
    @staticmethod
    def write_results_to_file(history, file_name=None):
        """
        Writes the conversation history to a file in Markdown format.
        If no filename is specified, the filename is generated using the current time.
        """
        import os, time
        if file_name is None:
            file_name = 'chatGPT_report' + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.md'
        os.makedirs('./gpt_log/', exist_ok=True)
        with open(f'./gpt_log/{file_name}', 'w', encoding='utf8') as f:
            f.write('# chatGPT report\n')
            for i, content in enumerate(history):
                try:
                    if type(content) != str: content = str(content)
                except:
                    continue
                if i % 2 == 0:
                    f.write('## ')
                f.write(content)
                f.write('\n\n')
        res = 'The above material has been written in ' + os.path.abspath(f'./analyzer_logs/{file_name}')
        print(res)
        return res

    @staticmethod
    def analyze_project(file_manifest, project_folder, chatbot, history):
        print('begin analysis on:', file_manifest)
        for index, fp in enumerate(file_manifest):
            status = 'Normal'
            with open(fp, 'r', encoding='utf-8') as f:
                file_content = f.read()

            prefix = "Next, please analyze the following project file by file" if index == 0 else ""
            i_say = prefix + f'Please make a summary of the following program file. File name: {os.path.relpath(fp, project_folder)}. Source code: ```{file_content}```'
            i_say_show_user = prefix + f'[{index}/{len(file_manifest)}] Please make a summary of the following program file: {os.path.abspath(fp)}'
            chatbot.append((i_say_show_user, "[Local Message] waiting gpt response."))
            yield chatbot, history, status

            # ** gpt request **
            gpt_say = yield from ChatGPTService.predict_no_ui_but_counting_down(i_say, i_say_show_user, chatbot, history=[])

            chatbot[-1] = (i_say_show_user, gpt_say)
            history.append(i_say_show_user)
            history.append(gpt_say)
            yield chatbot, history, status
            time.sleep(2)

        all_file = ', '.join([os.path.relpath(fp, project_folder) for index, fp in enumerate(file_manifest)])
        i_say = f'Based on your own analysis above, make a summary of the overall functionality and architecture of the program. Then use a markdown table to explain the functionality of each file (including {all_file}).'
        chatbot.append((i_say, "[Local Message] waiting gpt response."))
        yield chatbot, history, 'Normal'

        # ** gpt request **
        gpt_say = yield from ChatGPTService.predict_no_ui_but_counting_down(i_say, i_say, chatbot, history=history)

        chatbot[-1] = (i_say, gpt_say)
        history.append(i_say)
        history.append(gpt_say)
        yield chatbot, history, status
        res = CodeAnalyzerService.write_results_to_file(history)
        chatbot.append(("Completed? ", res))
        yield chatbot, history, status

    @staticmethod
    def analyze_python_project(txt, chatbot, history):
        history = []
        import glob, os
        if os.path.exists(txt):
            project_folder = txt
        else:
            if txt == "": txt = 'Empty input'
            LLMService.report_execption(chatbot, history, a=f"Project analyzed: {txt}", b=f"Cannot find project / no permission to read: {txt}")
            yield chatbot, history, 'Normal'
            return
        file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.py', recursive=True)]
        if len(file_manifest) == 0:
            LLMService.report_execption(chatbot, history, a=f"Project analyzed: {txt}", b=f"Cannnot find any .py file: {txt}")
            yield chatbot, history, 'Normal'
            return
        yield from CodeAnalyzerService.analyze_project(file_manifest, project_folder, chatbot, history)

    @staticmethod
    def ask_question():
        pass

    @staticmethod
    def test_formatting(txt, chatbot, history):
        msg = r"""
程序整体功能：CodeAnalyzerGPT工程是一个用于自动化代码分析和评审的工具。它使用了OpenAI的GPT模型对代码进行分析，然后根据一定的规则和标准来评价代码的质量和合规性。

程序的构架包含以下几个模块：

1. CodeAnalyzerGPT: 主程序模块，包含了代码分析和评审的主要逻辑。

2. analyzer: 包含了代码分析程序的具体实现。

每个文件的功能可以总结为下表：

| 文件名 | 功能描述 |
| --- | --- |
| C:\github\!CodeAnalyzerGPT\CodeAnalyzerGPT\CodeAnalyzerGPT.py | 主程序入口，调用各种处理逻辑和输出结果 |
| C:\github\!CodeAnalyzerGPT\CodeAnalyzerGPT\analyzer\code_analyzer.py | 代码分析器，包含了对代码文本的解析和分析逻辑 |
| C:\github\!CodeAnalyzerGPT\CodeAnalyzerGPT\analyzer\code_segment.py | 对代码文本进行语句和表达式的分段处理 |


Overall, this program consists of the following files:
- `main.py`: This is the primary script of the program which uses NLP to analyze and summarize Python code.
- `model.py`: This file defines the `CodeModel` class that is used by `main.py` to model the code as graphs and performs operations on them.
- `parser.py`: This file contains custom parsing functions used by `model.py`.
- `test/`: This directory contains test scripts for `model.py` and `util.py`
- `util.py`: This file provides utility functions for the program such as getting the root directory of the project and reading configuration files.

| File | Functionality |
|------|---------------|
| main.py | Provides the primary script for the program. Analyzes and summarizes Python code using NLP. |
| model.py | Defines the `CodeModel` class that models the code as graphs and performs operations on them. |
| parser.py | Contains custom parsing functions used by `model.py`. |
| test/ | Contains test scripts for `model.py` and `util.py` |
| util.py | Provides utility functions such as getting the root directory of the project and reading configuration files. |

`util.py` specifically has two functions:

| Function | Input | Output | Functionality |
|----------|-------|--------|---------------|
| `get_project_root()` | None | String containing the path of the parent directory of the script itself | Finds the path of the parent directory of the script itself |
| `get_config()` | None | Dictionary containing the contents of `config.yaml` and `config_secret.yaml`, merged together (with `config_secret.yaml` overwriting any keys with the same name in `config.yaml`) | Reads and merges two YAML configuration files (`config.yaml` and `config_secret.yaml`) located in the `config` directory in the parent directory of the script. Returns the resulting dictionary. |The above material has been written in C:\github\!CodeAnalyzerGPT\CodeAnalyzerGPT\analyzer_logs\chatGPT_report2023-04-07-14-11-55.md

    """
        chatbot.append(("test prompt query", msg))
        yield chatbot, history, 'Normal'
