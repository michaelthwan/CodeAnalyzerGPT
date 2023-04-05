import os
import gradio as gr
import logging

# TODO config.py

initial_prompt = "Be a code explainer"
title_html = "<h1 align=\"center\">CodeAnalyzerGPT</h1>"
os.makedirs("analyzer_logs", exist_ok=True)

if __name__ == '__main__':
    with gr.Blocks() as demo:
        gr.HTML(title_html)
        with gr.Row().style(equal_height=True):
            with gr.Column(scale=1):
                with gr.Row():
                    txt = gr.Textbox(show_label=False, placeholder="Input your project folder")
                with gr.Row():
                    submitBtn = gr.Button("Submit", variant="primary")
                with gr.Row():
                    resetBtn = gr.Button("Reset", variant="secondary")
                    resetBtn.style(size="sm")
                    stopBtn = gr.Button("Stop", variant="secondary")
                    stopBtn.style(size="sm")
                with gr.Row():
                    gr.Button("Analyze code base", variant="primary")
            with gr.Column(scale=3):
                chatbot = gr.Chatbot()
                history = gr.State([])

demo.title = "CodeAnalyzerGPT"
demo.launch()
