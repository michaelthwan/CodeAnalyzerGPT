import gradio as gr

from analyzer.code_analyzer import CodeAnalyzerService

title_html = "<h1 align=\"center\">CodeAnalyzerGPT</h1>"

functions = {
    "Analyze code base": {
        "function": CodeAnalyzerService.analyze_python_project
    },
    "Ask": {
        "function": CodeAnalyzerService.ask_question
    }
}

cancel_handles = []


class GradioUIService:
    @staticmethod
    def get_gradio_ui():
        with gr.Blocks() as demo:
            gr.HTML(title_html)
            with gr.Row().style(equal_height=True):
                with gr.Column(scale=1):
                    with gr.Row():
                        txt = gr.Textbox(show_label=False, placeholder="Input your project folder").style(container=False)
                    with gr.Row():
                        functions["Analyze code base"]["btn"] = gr.Button("Analyze code base", variant="primary")
                    with gr.Row():
                        txt_qa = gr.Textbox(show_label=False, placeholder="Ask questions").style(container=False)
                    with gr.Row():
                        functions["Ask"]["btn"] = gr.Button("Ask", variant="primary")
                    with gr.Row():
                        reset_btn = gr.Button("Reset", variant="secondary")
                        reset_btn.style(size="sm")
                        stop_btn = gr.Button("Stop", variant="secondary")
                        stop_btn.style(size="sm")
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot()
                    chatbot.style(height=1000)
                    history = gr.State([])
            input_combo = [txt, chatbot, history]
            output_combo = [chatbot, history]
            # predict_args = dict(fn=ChatGPTService.ask_chatgpt, inputs=input_combo, outputs=output_combo)
            for fn_key in functions:
                click_handle = functions[fn_key]["btn"].click(functions[fn_key]["function"], input_combo, output_combo)
                cancel_handles.append(click_handle)
        demo.title = "CodeAnalyzerGPT"
        return demo
