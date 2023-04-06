import json
import logging
import traceback

import requests

from analyzer.util import get_config

timeout_bot_msg = 'Request timeout. Network error'
LLM_MODEL = "gpt-3.5-turbo"
SYSTEM_PROMPT = "be a coding copilot and assist developer's code reading."

# This piece of code heavily reference
# - https://github.com/GaiZhenbiao/ChuanhuChatGPT
# - https://github.com/binary-husky/chatgpt_academic


config = get_config()


class LLMService:
    @staticmethod
    def report_execption(chatbot, history, a, b):
        chatbot.append((a, b))
        history.append(a)
        history.append(b)

    @staticmethod
    def get_full_error(chunk, stream_response):
        while True:
            try:
                chunk += next(stream_response)
            except:
                break
        return chunk

    @staticmethod
    def generate_payload(inputs, history, stream):
        API_KEY = config['openai_api_key']
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        conversation_cnt = len(history) // 2

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if conversation_cnt:
            for index in range(0, 2 * conversation_cnt, 2):
                what_i_have_asked = {}
                what_i_have_asked["role"] = "user"
                what_i_have_asked["content"] = history[index]
                what_gpt_answer = {}
                what_gpt_answer["role"] = "assistant"
                what_gpt_answer["content"] = history[index + 1]
                if what_i_have_asked["content"] != "":
                    if what_gpt_answer["content"] == "": continue
                    if what_gpt_answer["content"] == timeout_bot_msg: continue
                    messages.append(what_i_have_asked)
                    messages.append(what_gpt_answer)
                else:
                    messages[-1]['content'] = what_gpt_answer['content']

        what_i_ask_now = {}
        what_i_ask_now["role"] = "user"
        what_i_ask_now["content"] = inputs
        messages.append(what_i_ask_now)

        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": 1.0,
            "top_p": 1.0,
            "n": 1,
            "stream": stream,
            "presence_penalty": 0,
            "frequency_penalty": 0,
        }

        print(f" {LLM_MODEL} : {conversation_cnt} : {inputs}")
        return headers, payload

    @staticmethod
    def predict(inputs, chatbot=[], history=[]):
        stream = True  # FIXME: better handling
        if stream:
            raw_input = inputs
            logging.info(f'[raw_input] {raw_input}')
            chatbot.append((inputs, ""))
            yield chatbot, history, "Calling..."

        headers, payload = LLMService.generate_payload(inputs, history, stream)
        history.append(inputs)
        history.append(" ")

        retry = 0
        while True:
            try:
                response = requests.post(config['openai']['api_url'],
                                         headers=headers,
                                         json=payload,
                                         stream=True,
                                         timeout=config['openai']['timeout_sec'])
                break
            except:
                retry += 1
                chatbot[-1] = ((chatbot[-1][0], timeout_bot_msg))
                max_retry = config['openai']['max_retry']
                retry_msg = f"Retrying... ({retry}/{max_retry}) ……" if max_retry > 0 else ""
                yield chatbot, history, "Request Timeout" + retry_msg
                if retry > max_retry: raise TimeoutError

        gpt_replying_buffer = ""

        is_head_of_the_stream = True
        if stream:
            stream_response = response.iter_lines()
            while True:
                chunk = next(stream_response)
                # print(chunk.decode()[6:])
                if is_head_of_the_stream:
                    # datastream's first frame doesn't carry content
                    is_head_of_the_stream = False
                    continue

                if chunk:
                    try:
                        if len(json.loads(chunk.decode()[6:])['choices'][0]["delta"]) == 0:
                            # define the end of the stream. gpt_replying_buffer is also finished.
                            logging.info(f'[response] {gpt_replying_buffer}')
                            break
                        # handle the main body of the stream
                        chunkjson = json.loads(chunk.decode()[6:])
                        status_text = f"finish_reason: {chunkjson['choices'][0]['finish_reason']}"
                        # If throw exception here, usually because the text is too long, see the output of get_full_error
                        gpt_replying_buffer = gpt_replying_buffer + json.loads(chunk.decode()[6:])['choices'][0]["delta"]["content"]
                        history[-1] = gpt_replying_buffer
                        chatbot[-1] = (history[-2], history[-1])
                        yield chatbot, history, status_text

                    except Exception as e:
                        traceback.print_exc()
                        yield chatbot, history, "Wrong Json format"
                        chunk = LLMService.get_full_error(chunk, stream_response)
                        error_msg = chunk.decode()
                        if "reduce the length" in error_msg:
                            chatbot[-1] = (chatbot[-1][0], "[Local Message] Input (or history) is too long, please reduce input or clear history by refreshing this page.")
                            history = []
                        elif "Incorrect API key" in error_msg:
                            chatbot[-1] = (chatbot[-1][0], "[Local Message] Incorrect API key provided.")
                        elif "exceeded your current quota" in error_msg:
                            chatbot[-1] = (chatbot[-1][0], "[Local Message] You exceeded your current quota in OpenAI")
                        else:
                            def regular_txt_to_markdown(text):
                                text = text.replace('\n', '\n\n')
                                text = text.replace('\n\n\n', '\n\n')
                                text = text.replace('\n\n\n', '\n\n')
                                return text

                            tb_str = '```\n' + traceback.format_exc() + '```'
                            chatbot[-1] = (chatbot[-1][0], f"[Local Message] Exception \n\n{tb_str} \n\n{regular_txt_to_markdown(chunk.decode()[4:])}")
                        yield chatbot, history, "Json exception" + error_msg
                        return
