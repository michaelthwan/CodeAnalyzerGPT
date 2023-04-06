import json
import os
import re
import threading
import time
import traceback
import requests

from analyzer.llm_service import LLMService
from analyzer.util import get_config

timeout_bot_msg = 'Request timeout. Network error'
LLM_MODEL = "gpt-3.5-turbo"
config = get_config()


class ChatGPTService:
    @staticmethod
    def get_reduce_token_percent(text):
        try:
            pattern = r"(\d+)\s+tokens\b"
            match = re.findall(pattern, text)
            EXCEED_ALLO = 500
            max_limit = float(match[0]) - EXCEED_ALLO
            current_tokens = float(match[1])
            ratio = max_limit / current_tokens
            assert ratio > 0 and ratio < 1
            return ratio, str(int(current_tokens - max_limit))
        except:
            return 0.5, 'Unknown'

    @staticmethod
    def predict_no_ui_but_counting_down(i_say, i_say_show_user, chatbot, history=[], long_connection=True):

        TIMEOUT_SECONDS, MAX_RETRY = config['openai']['timeout_sec'], config['openai']['max_retry']
        # When multi-threaded, you need a mutable structure to pass information between different threads
        # list is the simplest mutable structure, we put gpt output in the first position, the second position to pass the error message
        mutable_list = [None, '']

        # multi-threading worker
        def mt(i_say, history):
            while True:
                try:
                    mutable_list[0] = ChatGPTService.predict_no_ui_long_connection(inputs=i_say, history=history)
                    # if long_connection:
                    #     mutable_list[0] = predict_no_ui_long_connection(inputs=i_say, top_p=top_p, temperature=temperature, history=history, sys_prompt=sys_prompt)
                    # else:
                    #     mutable_list[0] = predict_no_ui(inputs=i_say, top_p=top_p, temperature=temperature, history=history, sys_prompt=sys_prompt)
                    break
                except ConnectionAbortedError as token_exceeded_error:
                    # Try to calculate the ratio and keep as much text as possible
                    p_ratio, n_exceed = ChatGPTService.get_reduce_token_percent(str(token_exceeded_error))
                    if len(history) > 0:
                        history = [his[int(len(his) * p_ratio):] for his in history if his is not None]
                    else:
                        i_say = i_say[:int(len(i_say) * p_ratio)]
                    mutable_list[1] = f'Warning: text too long will be truncated. Token exceeded：{n_exceed}，Truncation ratio：{(1 - p_ratio):.0%}。'
                except TimeoutError as e:
                    mutable_list[0] = '[Local Message] Request timeout.'
                    raise TimeoutError
                except Exception as e:
                    mutable_list[0] = f'[Local Message] Exception: {str(e)}.'
                    raise RuntimeError(f'[Local Message] Exception: {str(e)}.')

        # Create a new thread to make http requests
        thread_name = threading.Thread(target=mt, args=(i_say, history))
        thread_name.start()
        # The original thread is responsible for continuously updating the UI, implementing a timeout countdown, and waiting for the new thread's task to complete
        cnt = 0
        while thread_name.is_alive():
            cnt += 1
            chatbot[-1] = (i_say_show_user, f"[Local Message] {mutable_list[1]}waiting gpt response {cnt}/{TIMEOUT_SECONDS * 2 * (MAX_RETRY + 1)}" + ''.join(['.'] * (cnt % 4)))
            yield chatbot, history, 'Normal'
            time.sleep(1)
        # Get the output of gpt out of the mutable
        gpt_say = mutable_list[0]
        if gpt_say == '[Local Message] Failed with timeout.': raise TimeoutError
        return gpt_say

    @staticmethod
    def predict_no_ui_long_connection(inputs, history=[], observe_window=None):
        """
            Send to chatGPT and wait for a reply, all at once, without showing the intermediate process. But the internal method of stream is used.
            observe_window: used to pass the output across threads, most of the time just for the fancy visual effect, just leave it empty
        """
        headers, payload = LLMService.generate_payload(inputs, history, stream=True)

        retry = 0
        while True:
            try:
                # make a POST request to the API endpoint, stream=False
                response = requests.post(config['openai']['api_url'], headers=headers,
                                         json=payload, stream=True, timeout=config['openai']['timeout_sec']
                                         )
                break
            except requests.exceptions.ReadTimeout as e:
                max_retry = config['openai']['max_retry']
                retry += 1
                traceback.print_exc()
                if retry > max_retry:
                    raise TimeoutError
                if max_retry != 0:
                    print(f'Request timeout. Retrying ({retry}/{max_retry}) ...')

        stream_response = response.iter_lines()
        result = ''
        while True:
            try:
                chunk = next(stream_response).decode()
            except StopIteration:
                break
            if len(chunk) == 0: continue
            if not chunk.startswith('data:'):
                error_msg = LLMService.get_full_error(chunk.encode('utf8'), stream_response).decode()
                if "reduce the length" in error_msg:
                    raise ConnectionAbortedError("OpenAI rejected the request:" + error_msg)
                else:
                    raise RuntimeError("OpenAI rejected the request: " + error_msg)
            json_data = json.loads(chunk.lstrip('data:'))['choices'][0]
            delta = json_data["delta"]
            if len(delta) == 0: break
            if "role" in delta: continue
            if "content" in delta:
                result += delta["content"]
                print(delta["content"], end='')
                if observe_window is not None: observe_window[0] += delta["content"]
            else:
                raise RuntimeError("Unexpected Json structure: " + delta)
        if json_data['finish_reason'] == 'length':
            raise ConnectionAbortedError("Completed normally with insufficient Tokens")
        return result


class BotService:
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
        res = BotService.write_results_to_file(history)
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
        yield from BotService.analyze_project(file_manifest, project_folder, chatbot, history)

    @staticmethod
    def ask_question():
        pass
