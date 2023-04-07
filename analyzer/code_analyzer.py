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
            gpt_say = yield from ChatGPTService.predict_no_ui_but_counting_down(i_say, i_say_show_user, chatbot, history=[])  # 带超时倒计时

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
        gpt_say = yield from ChatGPTService.predict_no_ui_but_counting_down(i_say, i_say, chatbot, history=history)  # 带超时倒计时

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
