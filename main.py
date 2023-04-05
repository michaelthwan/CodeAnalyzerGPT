import os
import gradio as gr
from analyzer.util import get_config
from analyzer.code_analyzer import analyze_project
from analyzer.llm_service import LLMService

initial_prompt = "Be a code explainer"
title_html = "<h1 align=\"center\">CodeAnalyzerGPT</h1>"
os.makedirs("analyzer_logs", exist_ok=True)

functions = {"Analyze code base": {
    "Function": analyze_project
}}
cancel_handles = []

if __name__ == '__main__':
    config = get_config()
    with gr.Blocks() as demo:
        gr.HTML(title_html)
        with gr.Row().style(equal_height=True):
            with gr.Column(scale=1):
                with gr.Row():
                    txt = gr.Textbox(show_label=False, placeholder="Input your project folder").style(container=False)
                with gr.Row():
                    for fn_key in functions:
                        functions[fn_key]["btn"] = gr.Button("Analyze code base", variant="primary")
                with gr.Row():
                    txt_qa = gr.Textbox(show_label=False, placeholder="Ask questions").style(container=False)
                with gr.Row():
                    gr.Button("Ask", variant="primary")
                with gr.Row():
                    reset_btn = gr.Button("Reset", variant="secondary")
                    reset_btn.style(size="sm")
                    stop_btn = gr.Button("Stop", variant="secondary")
                    stop_btn.style(size="sm")
            with gr.Column(scale=3):
                chatbot = gr.Chatbot()
                history = gr.State([])
        input_combo = [txt, chatbot, history]
        output_combo = [chatbot, history]
        predict_args = dict(fn=LLMService.predict, inputs=input_combo, outputs=output_combo)
        for fn_key in functions:
            click_handle = functions[fn_key]["btn"].click(LLMService.predict, input_combo, output_combo)
            cancel_handles.append(click_handle)

    demo.title = "CodeAnalyzerGPT"
    demo.queue(concurrency_count=config['gradio']['concurrent']).launch(share=True)
