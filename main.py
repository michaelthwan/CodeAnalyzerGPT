import os
import gradio as gr
from util import get_config
import logging

initial_prompt = "Be a code explainer"
title_html = "<h1 align=\"center\">CodeAnalyzerGPT</h1>"
os.makedirs("analyzer_logs", exist_ok=True)

if __name__ == '__main__':
    config = get_config()
    with gr.Blocks() as demo:
        gr.HTML(title_html)
        with gr.Row().style(equal_height=True):
            with gr.Column(scale=1):
                with gr.Row():
                    txt = gr.Textbox(show_label=False, placeholder="Input your project folder").style(container=False)
                with gr.Row():
                    gr.Button("Analyze code base", variant="primary")
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

    demo.title = "CodeAnalyzerGPT"
    demo.queue(concurrency_count=config['gradio']['concurrent']) \
        .launch(share=True)
