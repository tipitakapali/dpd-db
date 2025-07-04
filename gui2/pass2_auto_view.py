import flet as ft

from gui2.pass2_auto_control import Pass2AutoController
from gui2.toolkit import ToolKit


class Pass2AutoView(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
    ) -> None:
        super().__init__(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[],
            spacing=5,
        )
        self.page: ft.Page = page
        self.controller = Pass2AutoController(
            self,
            toolkit,
        )
        self.controller.ui = self

        # Define constants
        LABEL_WIDTH: int = 150
        COLUMN_WIDTH: int = 700

        # Define controls
        self._message_field = ft.Text(
            "",
            expand=True,
            color=ft.Colors.BLUE_200,
            selectable=True,
        )
        self.book_options = [
            ft.dropdown.Option(key=item, text=item)
            for item in self.controller.sc_books_list
        ]
        self.books_dropdown = ft.Dropdown(
            autofocus=True,
            options=self.book_options,
            width=300,
            text_size=14,
            border_color=ft.Colors.BLUE_200,
        )
        self.auto_processed_count_field = ft.TextField(
            "",
            expand=True,
        )
        self.word_in_text_field = ft.TextField(
            "",
            width=COLUMN_WIDTH,
            expand=True,
        )
        self.ai_results_field = ft.TextField(
            "",
            width=COLUMN_WIDTH,
            multiline=True,
            expand=True,
        )

        self.controls.extend(
            [
                ft.Row(
                    controls=[
                        ft.Text("", width=LABEL_WIDTH),
                        self._message_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("book", width=LABEL_WIDTH),
                        self.books_dropdown,
                        ft.ElevatedButton(
                            "AutoProcess Book",
                            on_click=self.handle_book_click,
                        ),
                        ft.ElevatedButton(
                            "Stop",
                            on_click=self.handle_stop_click,
                        ),
                        ft.ElevatedButton(
                            "Clear",
                            on_click=self.handle_clear_click,
                        ),
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("auto processed", width=LABEL_WIDTH),
                        self.auto_processed_count_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("word in text", width=LABEL_WIDTH),
                        self.word_in_text_field,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Text("ai results", width=LABEL_WIDTH),
                        self.ai_results_field,
                    ]
                ),
            ]
        )

    def handle_book_click(self, e: ft.ControlEvent):
        if self.books_dropdown.value:
            self.controller.auto_process_book(self.books_dropdown.value)

    def handle_stop_click(self, e):
        self.controller.stop_flag = True
        self.update_message("stopped")
        self.controller.processed_count = 0

    def handle_clear_click(self, e):
        self.clear_all_fields()

    def update_message(self, message: str):
        self._message_field.value = message
        self.page.update()

    def update_ai_results(self, results: str):
        self.ai_results_field.value = results
        self.page.update()

    def update_word_in_text(self, word: str):
        self.word_in_text_field.value = word
        self.page.update()

    def update_auto_processed_count(self, count: str):
        self.auto_processed_count_field.value = str(count)
        self.page.update()

    def clear_all_fields(self):
        self._message_field.value = ""
        self.auto_processed_count_field.value = ""
        self.books_dropdown.value = ""
        self.ai_results_field.value = ""
        self.word_in_text_field.value = ""
        self.page.update()
