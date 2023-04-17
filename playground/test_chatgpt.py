import os

from analyzer.chatgpt_service import ChatGPTService


def call_openai():
    file_path = r"C:\github\!CodeAnalyzerGPT\CodeAnalyzerGPT\analyzer\gradio_ui_service.py"
    file_name = os.path.basename(file_path)
    pf_md = ""
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    i_say = f"""
Please describe each function with format

- <method name>(<input>) -> <output>:
<description> 
- <method name>(<input>) -> <output>:
<description> 

In the description, mention important called method as well.

File name: {file_name}. Source code: ```{file_content}
```
    """
    i_say_show_user = ""
    chatbot = []
    gpt_say = yield from ChatGPTService.predict_no_ui_but_counting_down(pf_md, i_say, i_say_show_user, chatbot, history=[])
    yield gpt_say


if __name__ == '__main__':
    gpt_say = next(call_openai())
    print(gpt_say)
