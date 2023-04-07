import gradio as gr
import markdown

from analyzer.code_analyzer import CodeAnalyzerService

title_html = "<h1 align=\"center\">CodeAnalyzerGPT</h1>"

functions = {
    "Analyze code base": {
        "function": CodeAnalyzerService.analyze_python_project
    },
    "Ask": {
        "function": CodeAnalyzerService.ask_question
    },
    "Test formatting": {
        "function": CodeAnalyzerService.test_formatting
    },
}

cancel_handles = []


class GradioUIService:
    def format_io(self, y):
        """
        Convert the input and output to HTML format.
            Paragraphize the input part of the last item in y,
            and convert the Markdown and mathematical formula in the output part to HTML format.
        """

        def text_divide_paragraph(text):
            """
            Separate the text according to the paragraph separator and generate HTML code with paragraph tags.
            """
            if '```' in text:
                return text
            else:
                lines = text.split("\n")
                for i, line in enumerate(lines):
                    lines[i] = lines[i].replace(" ", "&nbsp;")
                text = "</br>".join(lines)
                return text

        def close_up_code_segment_during_stream(gpt_reply):
            """
            Handling when the GPT output is cut in half
            Add '```' at the end of the output if the output is not complete.
            """
            # guard pattern for normal cases
            if '```' not in gpt_reply:
                return gpt_reply
            if gpt_reply.endswith('```'):
                return gpt_reply

            # otherwise
            segments = gpt_reply.split('```')
            n_mark = len(segments) - 1
            if n_mark % 2 == 1:
                return gpt_reply + '\n```'
            else:
                return gpt_reply

        def markdown_convertion(txt):
            """
            Convert markdown text to HTML format. If there are math formulas, convert them to HTML format first.
            """
            pre = '<div class="markdown-body">'
            suf = '</div>'
            if ('$' in txt) and ('```' not in txt):
                return pre + markdown.markdown(txt, extensions=['fenced_code', 'tables']) + '<br><br>' + markdown.markdown(convert_math(txt, splitParagraphs=False),
                                                                                                                           extensions=['fenced_code', 'tables']) + suf
            else:
                return pre + markdown.markdown(txt, extensions=['fenced_code', 'tables']) + suf

        if y is None or y == []: return []
        i_ask, gpt_reply = y[-1]
        i_ask = text_divide_paragraph(i_ask)
        gpt_reply = close_up_code_segment_during_stream(gpt_reply)
        y[-1] = (
            None if i_ask is None else markdown.markdown(i_ask, extensions=['fenced_code', 'tables']),
            None if gpt_reply is None else markdown_convertion(gpt_reply)
        )
        return y

    @staticmethod
    def get_theme():
        try:
            # color_er = gr.themes.utils.colors.pink
            set_theme = gr.themes.Default(
                primary_hue=gr.themes.utils.colors.orange,
                neutral_hue=gr.themes.utils.colors.gray,
                font=["Helvetica Neue", "Helvetica", "Arial", "sans-serif"],
                font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "Consolas", "ui-monospace", "monospace"]
            )
            # set_theme.set(
            #     # Colors
            #     input_background_fill_dark="*neutral_800",
            #     # Transition
            #     button_transition="none",
            #     # Shadows
            #     button_shadow="*shadow_drop",
            #     button_shadow_hover="*shadow_drop_lg",
            #     button_shadow_active="*shadow_inset",
            #     input_shadow="0 0 0 *shadow_spread transparent, *shadow_inset",
            #     input_shadow_focus="0 0 0 *shadow_spread *secondary_50, *shadow_inset",
            #     input_shadow_focus_dark="0 0 0 *shadow_spread *neutral_700, *shadow_inset",
            #     checkbox_label_shadow="*shadow_drop",
            #     block_shadow="*shadow_drop",
            #     form_gap_width="1px",
            #     # Button borders
            #     input_border_width="1px",
            #     input_background_fill="white",
            #     # Gradients
            #     stat_background_fill="linear-gradient(to right, *primary_400, *primary_200)",
            #     stat_background_fill_dark="linear-gradient(to right, *primary_400, *primary_600)",
            #     error_background_fill=f"linear-gradient(to right, {color_er.c100}, *background_fill_secondary)",
            #     error_background_fill_dark="*background_fill_primary",
            #     checkbox_label_background_fill="linear-gradient(to top, *neutral_50, white)",
            #     checkbox_label_background_fill_dark="linear-gradient(to top, *neutral_900, *neutral_800)",
            #     checkbox_label_background_fill_hover="linear-gradient(to top, *neutral_100, white)",
            #     checkbox_label_background_fill_hover_dark="linear-gradient(to top, *neutral_900, *neutral_800)",
            #     button_primary_background_fill="linear-gradient(to bottom right, *primary_100, *primary_300)",
            #     button_primary_background_fill_dark="linear-gradient(to bottom right, *primary_500, *primary_600)",
            #     button_primary_background_fill_hover="linear-gradient(to bottom right, *primary_100, *primary_200)",
            #     button_primary_background_fill_hover_dark="linear-gradient(to bottom right, *primary_500, *primary_500)",
            #     button_primary_border_color_dark="*primary_500",
            #     button_secondary_background_fill="linear-gradient(to bottom right, *neutral_100, *neutral_200)",
            #     button_secondary_background_fill_dark="linear-gradient(to bottom right, *neutral_600, *neutral_700)",
            #     button_secondary_background_fill_hover="linear-gradient(to bottom right, *neutral_100, *neutral_100)",
            #     button_secondary_background_fill_hover_dark="linear-gradient(to bottom right, *neutral_600, *neutral_600)",
            #     button_cancel_background_fill=f"linear-gradient(to bottom right, {color_er.c100}, {color_er.c200})",
            #     button_cancel_background_fill_dark=f"linear-gradient(to bottom right, {color_er.c600}, {color_er.c700})",
            #     button_cancel_background_fill_hover=f"linear-gradient(to bottom right, {color_er.c100}, {color_er.c100})",
            #     button_cancel_background_fill_hover_dark=f"linear-gradient(to bottom right, {color_er.c600}, {color_er.c600})",
            #     button_cancel_border_color=color_er.c200,
            #     button_cancel_border_color_dark=color_er.c600,
            #     button_cancel_text_color=color_er.c600,
            #     button_cancel_text_color_dark="white",
            # )
        except Exception as e:
            set_theme = None
            print(f'please upgrade to newer version of gradio {e}')
        return set_theme

    @staticmethod
    def get_css():
        css = """
/* Set the outer margins of the table to 1em, merge the borders between internal cells, and display empty cells. */
.markdown-body table {
    margin: 1em 0;
    border-collapse: collapse;
    empty-cells: show;
}

/* Set the inner margin of the table cell to 5px, the border thickness to 1.2px, and the color to --border-color-primary. */
.markdown-body th, .markdown-body td {
    border: 1.2px solid var(--border-color-primary);
    padding: 5px;
}

/* Set the table header background color to rgba(175,184,193,0.2) and transparency to 0.2. */
.markdown-body thead {
    background-color: rgba(175,184,193,0.2);
}

/* Set the padding of the table header cell to 0.5em and 0.2em. */
.markdown-body thead th {
    padding: .5em .2em;
}

/* Remove the default padding of the list prefix to align it with the text line. */
.markdown-body ol, .markdown-body ul {
    padding-inline-start: 2em !important;
}

/* Set the style of the chat bubble, including the radius, the maximum width, and the shadow. */
[class *= "message"] {
    border-radius: var(--radius-xl) !important;
    /* padding: var(--spacing-xl) !important; */
    /* font-size: var(--text-md) !important; */
    /* line-height: var(--line-md) !important; */
    /* min-height: calc(var(--text-md)*var(--line-md) + 2*var(--spacing-xl)); */
    /* min-width: calc(var(--text-md)*var(--line-md) + 2*var(--spacing-xl)); */
}
[data-testid = "bot"] {
    max-width: 95%;
    /* width: auto !important; */
    border-bottom-left-radius: 0 !important;
}
[data-testid = "user"] {
    max-width: 100%;
    /* width: auto !important; */
    border-bottom-right-radius: 0 !important;
}

/* Set the background of the inline code to light gray, set the radius and spacing. */
.markdown-body code {
    display: inline;
    white-space: break-spaces;
    border-radius: 6px;
    margin: 0 2px 0 2px;
    padding: .2em .4em .1em .4em;
    background-color: rgba(175,184,193,0.2);
}
/* Set the style of the code block, including the background color, the inner and outer margins, and the radius. */
.markdown-body pre code {
    display: block;
    overflow: auto;
    white-space: pre;
    background-color: rgba(175,184,193,0.2);
    border-radius: 10px;
    padding: 1em;
    margin: 1em 2em 1em 0.5em;
}
"""
        return css

    @staticmethod
    def get_gradio_ui():
        gr.Chatbot.postprocess = GradioUIService.format_io
        with gr.Blocks(theme=GradioUIService.get_theme(), css=GradioUIService.get_css()) as demo:
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
                        functions["Test formatting"]["btn"] = gr.Button("Test formatting")
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
