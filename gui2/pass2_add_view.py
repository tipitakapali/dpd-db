import copy

import flet as ft

from db.models import DpdHeadword
from gui2.dpd_fields import DpdFields
from gui2.dpd_fields_commentary import DpdCommentaryField
from gui2.dpd_fields_examples import DpdExampleField
from gui2.dpd_fields_functions import increment_lemma_1
from gui2.dpd_fields_lists import (
    COMPOUND_FIELDS,
    NO_CLONE_LIST,
    NO_SPLIT_LIST,
    PASS1_FIELDS,
    ROOT_FIELDS,
    WORD_FIELDS,
)
from gui2.mixins import PopUpMixin
from gui2.pass2_auto_control import Pass2AutoController
from gui2.pass2_file_manager import Pass2AutoFileManager

from gui2.toolkit import ToolKit
from scripts.backup.backup_dpd_headwords_and_roots import backup_dpd_headwords_and_roots
from tools.fast_api_utils import request_dpd_server
from tools.paths import ProjectPaths  # Import ProjectPaths
from tools.sandhi_contraction import SandhiContractionDict

LABEL_WIDTH = 250
BUTTON_WIDTH = 250
LABEL_COLOUR = ft.Colors.GREY_500
HIGHLIGHT_COLOUR = ft.Colors.BLUE_200


class Pass2AddView(ft.Column, PopUpMixin):
    def __init__(
        self,
        page: ft.Page,
        toolkit: ToolKit,
    ) -> None:
        # Main container column - does not scroll, expands vertically
        super().__init__(
            expand=True,  # Main column expands
            controls=[],  # Controls defined below
            spacing=5,
        )
        from gui2.test_manager import GuiTestManager

        self.page: ft.Page = page
        self.toolkit: ToolKit = toolkit

        self._db = self.toolkit.db_manager
        self._daily_log = self.toolkit.daily_log
        self.pass2_auto_controller = Pass2AutoController(self, self.toolkit)
        self.test_manager: GuiTestManager = self.toolkit.test_manager
        self.sandhi_manager = self.toolkit.sandhi_manager
        self.sandhi_dict: SandhiContractionDict = (
            self.sandhi_manager.get_sandhi_contractions_simple()
        )
        self.hyphenation_manager = self.toolkit.hyphenation_manager
        self.hyphenation_dict = self.hyphenation_manager.load_hyphenations_dict()
        self.history_manager = self.toolkit.history_manager

        self.dpd_fields: DpdFields
        self._pass2_auto_file_manager = Pass2AutoFileManager(self.toolkit)
        self.headword: DpdHeadword | None = None
        self.headword_original: DpdHeadword | None = None

        self._message_field = ft.TextField(
            "",
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
            border=ft.InputBorder.OUTLINE,
            color=ft.Colors.BLUE_200,
            expand_loose=True,
            expand=True,
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            hint_text="Messages",
            read_only=True,
            text_size=14,
            width=700,
        )
        self._next_pass2_auto_button = ft.ElevatedButton(
            "NextPass2Auto",
            on_click=self._click_load_next_pass2_entry,
        )
        self._enter_id_or_lemma_field = ft.TextField(
            "",
            autofocus=True,
            border_color=ft.Colors.BLUE_200,
            border_radius=20,
            expand_loose=True,
            expand=True,
            hint_style=ft.TextStyle(color=LABEL_COLOUR, size=10),
            hint_text="Enter ID or Lemma",
            on_submit=self._click_edit_headword,
            text_size=14,
            width=400,
        )
        self._clone_headword_button = ft.ElevatedButton(
            "Clone", on_click=self._click_clone_headword
        )
        self._split_headword_button = ft.ElevatedButton(
            "Split", on_click=self._click_split_headword
        )
        self._clear_all_button = ft.ElevatedButton(
            "Clear All", on_click=self._click_clear_all
        )
        self.update_sandhi_button = ft.ElevatedButton(
            "Update Sandhi", on_click=self._click_update_sandhi
        )
        self._update_with_ai_button = ft.ElevatedButton(
            "AiAutofill", on_click=self._click_update_with_ai
        )

        self._history_dropdown = ft.Dropdown(
            hint_text="History",
            hint_style=ft.TextStyle(color=ft.Colors.BLUE_200),
            options=[],
            expand=True,
            expand_loose=True,
            border_radius=20,
            text_size=14,
            on_change=self._handle_history_selection,
        )

        # --- Field Filter Radio Buttons ---
        self._filter_radios = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="all", label="All"),
                    ft.Radio(value="root", label="Root"),
                    ft.Radio(value="compound", label="Compound"),
                    ft.Radio(value="word", label="Word"),
                    ft.Radio(value="pass1", label="Pass1"),
                ]
            ),
            value="all",  # Default selection
            on_change=self._handle_filter_change,
        )

        # Define the Add to DB button as a member variable
        self._add_to_db_button = ft.ElevatedButton(
            "Add to DB",
            on_click=self._click_add_to_db,
            width=BUTTON_WIDTH,
        )
        self._top_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self._enter_id_or_lemma_field,
                            self._clone_headword_button,
                            self._split_headword_button,
                            self._next_pass2_auto_button,
                            self._clear_all_button,
                            self.update_sandhi_button,
                            self._update_with_ai_button,  # Add new button
                            self._history_dropdown,
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Row([self._message_field, self._filter_radios]),
                ],
            ),
            border=ft.Border(
                top=ft.BorderSide(1, HIGHLIGHT_COLOUR),
                bottom=ft.BorderSide(1, HIGHLIGHT_COLOUR),
            ),
            padding=10,
            alignment=ft.alignment.center,
        )

        # Build middle section using the new method
        self._middle_section = self._build_middle_section()

        # Populate history dropdown initially
        self._update_history_dropdown()

        self._bottom_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Test",
                                on_click=self._click_run_tests,
                                width=BUTTON_WIDTH,
                            ),
                            self._add_to_db_button,  # Use the member variable here
                            ft.ElevatedButton(
                                "Delete",
                                on_click=self._click_delete_from_db,
                                width=BUTTON_WIDTH,
                                on_hover=self._on_delete_hover,
                            ),
                            ft.ElevatedButton(
                                "Backup & Quit",
                                on_click=self._click_backup_db,
                                width=BUTTON_WIDTH,
                            ),  # Add backup button here
                        ],
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.all(10),
        )

        self.controls = [
            self._top_section,
            self._middle_section,
            self._bottom_section,
        ]

    def _on_delete_hover(self, e: ft.ControlEvent) -> None:
        e.control.bgcolor = ft.Colors.RED if e.data == "true" else None
        e.control.color = "white" if e.data == "true" else None
        e.control.update()

    def update_message(self, message: str) -> None:
        self._message_field.value = message
        self.page.update()

    def add_headword_to_examples_and_commentary(self):
        # add headword to example_1 example_2 and commentary
        if self.headword:
            example_1_field: DpdExampleField = self.dpd_fields.get_field("example_1")
            example_1_field.word_to_find_field.value = self.headword.lemma_1[:-1]
            example_1_field.bold_field.value = self.headword.lemma_clean[:-1]

            example_2_field: DpdExampleField = self.dpd_fields.get_field("example_2")
            example_2_field.word_to_find_field.value = self.headword.lemma_clean[:-1]

            commentary_field: DpdCommentaryField = self.dpd_fields.get_field(
                "commentary"
            )
            commentary_field.search_field_1.value = self.headword.lemma_clean[:-1]

    def _click_edit_headword(self, e: ft.ControlEvent) -> None:
        id_or_lemma = self._enter_id_or_lemma_field.value

        if id_or_lemma:
            headword = self._db.get_headword_by_id_or_lemma(id_or_lemma)
            if headword:
                self.clear_all_fields()
                self.headword = headword
                self._enter_id_or_lemma_field.value = headword.lemma_1  # show the word
                self.headword_original = copy.deepcopy(
                    headword
                )  # Store original for ID comparison
                self.dpd_fields.update_db_fields(headword)

                self.add_headword_to_examples_and_commentary()

                if self.headword is not None:
                    self.update_message(f"loaded {self.headword.lemma_clean}")

                    # load pass2auto if available
                    if (
                        self.headword.id is not None
                        and str(self.headword.id)
                        in self._pass2_auto_file_manager.responses
                    ):
                        to_add = self._pass2_auto_file_manager.get_headword(
                            str(self.headword.id)
                        )
                        self.dpd_fields.update_add_fields(to_add)
            else:
                self.update_message("headword not found")
        else:
            self.update_message("you're shooting blanks")

    def _click_clone_headword(self, e: ft.ControlEvent) -> None:
        """Fetches a headword and adds its data to empty fields in the current view."""
        id_or_lemma = self._enter_id_or_lemma_field.value

        if not id_or_lemma:
            self.update_message("Enter an ID or Lemma to clone from.")
            return

        headword_to_clone = self._db.get_headword_by_id_or_lemma(id_or_lemma)

        if not headword_to_clone:
            self.update_message(f"Headword '{id_or_lemma}' not found for cloning.")
            return

        cloned_count = 0
        for field_name, ui_field in self.dpd_fields.fields.items():
            if (
                hasattr(headword_to_clone, field_name)
                and field_name not in NO_CLONE_LIST
            ):
                # Check if the UI field is empty (or None)
                if not ui_field.value:
                    db_value = getattr(headword_to_clone, field_name)
                    if db_value is not None:  # Only clone non-None values
                        ui_field.value = db_value
                        cloned_count += 1

        self.update_message(
            f"Cloned {cloned_count} fields from {headword_to_clone.lemma_1}."
        )
        self.page.update()

    def _click_split_headword(self, e: ft.ControlEvent) -> None:
        """Copies current fields to a new ID, increments lemma_1, and clears specific fields."""
        current_lemma_1_field = self.dpd_fields.get_field("lemma_1")
        if not current_lemma_1_field or not current_lemma_1_field.value:
            self.update_message("Cannot split an entry with an empty lemma_1.")
            return

        old_lemma = current_lemma_1_field.value
        new_id = self._db.get_next_id()
        new_lemma = increment_lemma_1(old_lemma)

        cleared_count = 0
        for field_name, ui_field in self.dpd_fields.fields.items():
            if field_name == "id":
                ui_field.value = str(new_id)  # Ensure ID is string for TextField
            elif field_name == "lemma_1":
                ui_field.value = new_lemma
            elif field_name in NO_SPLIT_LIST:
                if ui_field.value:  # Only count if it actually had a value
                    cleared_count += 1
                ui_field.value = ""
                ui_field.error_text = None  # Clear errors too
            # else: field keeps its current value

        # Reset flags as this is effectively a new entry state
        self.dpd_fields.flags.reset()

        # Clear _add fields as they relate to the original word's auto-data
        self.dpd_fields.clear_fields(target="add")

        self.update_message(
            f"Split '{old_lemma}' into new entry '{new_lemma}' (ID: {new_id}). Cleared {cleared_count} fields."
        )
        self.page.update()
        current_lemma_1_field.focus()  # Focus back on lemma_1

    def _click_load_next_pass2_entry(self, e: ft.ControlEvent | None = None) -> None:
        """Load next pass2 entry into the view."""
        headword_id, pass2_auto_data = (
            self._pass2_auto_file_manager.get_next_headword_data()
        )

        if headword_id is not None:
            self.clear_all_fields()
            headword = self._db.get_headword_by_id(int(headword_id))

            if headword is not None:
                self.headword = headword
                self.headword_original = copy.deepcopy(headword)

                self.dpd_fields.update_db_fields(self.headword)
                self.dpd_fields.update_add_fields(pass2_auto_data)
                self.add_headword_to_examples_and_commentary()
            else:
                self.update_message(f"{headword_id}: headword not found")
                self._click_load_next_pass2_entry()

        else:
            self._message_field.value = "Current Pass2: None"
            self.clear_all_fields()

        self.update()

    def _click_clear_all(self, e: ft.ControlEvent):
        self.clear_all_fields()

    def _click_update_sandhi(self, e: ft.ControlEvent):
        self.update_message("updating sandhi... please wait...")
        self.sandhi_dict = self.sandhi_manager.update_contractions_simple()
        self.update_message("sandhi updated")

    def _handle_filter_change(self, e: ft.ControlEvent):
        """Handles changes in the field filter RadioGroup."""
        filter_type = e.control.value
        visible_fields = None  # Default to all

        if filter_type == "root":
            visible_fields = ROOT_FIELDS
        elif filter_type == "compound":
            visible_fields = COMPOUND_FIELDS
        elif filter_type == "word":
            visible_fields = WORD_FIELDS
        elif filter_type == "pass1":
            visible_fields = PASS1_FIELDS

        self.dpd_fields.filter_fields(visible_fields)
        self.page.update()

    def _update_history_dropdown(self):
        """Populates the history dropdown with the latest history."""
        history_items = self.history_manager.get_history()
        self._history_dropdown.options.clear()
        for item in history_items:
            self._history_dropdown.options.append(
                ft.dropdown.Option(
                    key=str(item.get("id")),  # Key must be string for Dropdown
                    text=f"{item.get('id')}: {item.get('lemma_1', 'N/A')}",
                )
            )
        self.page.update()  # Ensure dropdown updates visually

    def _handle_history_selection(self, e: ft.ControlEvent):
        """Loads the selected headword from history."""
        selected_id_str = e.control.value
        if selected_id_str:
            try:
                selected_id = int(selected_id_str)
                headword = self._db.get_headword_by_id(selected_id)
                if headword:
                    # Use existing logic similar to _click_edit_headword
                    self.clear_all_fields()
                    self.headword = headword
                    self.headword_original = copy.deepcopy(headword)
                    self.dpd_fields.update_db_fields(headword)
                    self.add_headword_to_examples_and_commentary()
                    self.update_message(
                        f"loaded {self.headword.lemma_clean} from history"
                    )
                    # Optionally load Pass2Auto data here if needed
                else:
                    self.update_message(
                        f"History item ID {selected_id} not found in DB"
                    )
            except ValueError:
                self.update_message("Invalid history item ID selected")
            finally:
                self._history_dropdown.value = None  # Reset dropdown selection
                self.page.update()

    # Add the new builder method
    def _build_middle_section(self) -> ft.Column:
        """Build and return the middle section with DpdFields."""
        self.dpd_fields = DpdFields(
            self, self._db, self.sandhi_dict, self.hyphenation_dict
        )
        middle_section = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=5,
            # Add any other specific Column properties if needed
        )
        self.dpd_fields.add_to_ui(middle_section, include_add_fields=True)
        return middle_section

    def clear_all_fields(
        self, e: ft.ControlEvent | None = None
    ) -> None:  # Add event arg if needed for button binding
        """Clear all fields by rebuilding the middle section."""
        # Rebuild middle section
        self._middle_section = self._build_middle_section()

        # Update view controls with new middle section
        self.controls = [self._top_section, self._middle_section, self._bottom_section]

        # Clear relevant top-section fields
        self._enter_id_or_lemma_field.value = ""
        self._enter_id_or_lemma_field.error_text = None
        self.headword = None  # Resetting the data model reference
        self._filter_radios.value = "all"  # Reset filter to 'all'
        self.headword_original = None  # Resetting the original data reference

        self.update_message("")  # Clear message field
        self.page.update()

    def _click_run_tests(self, e: ft.ControlEvent):
        """Run tests on current field values"""

        # Get the lemma_1 field and its value first
        lemma_1_field = self.dpd_fields.get_field("lemma_1")
        lemma_1_value = lemma_1_field.value if lemma_1_field else None

        # Check if lemma_1 has a value
        if lemma_1_value and str(lemma_1_value).strip():
            # lemma_1 has a value, proceed to get headword and run tests
            headword = (
                self.dpd_fields.get_current_headword()
            )  # Now we expect this to succeed
            if (
                headword
            ):  # Double check just in case get_current_headword has other failure modes
                self.dpd_fields.clear_messages()
                self.test_manager.run_all_tests(self, headword)
                # Change button color based on test results
                if hasattr(self.test_manager, "passed") and self.test_manager.passed:
                    self._add_to_db_button.color = ft.Colors.GREEN
                else:
                    self._add_to_db_button.color = None
            else:
                # Should ideally not happen if lemma_1 has value, but handle defensively
                self.update_message("Error creating headword")
                self._add_to_db_button.color = None
        else:
            # No lemma_1 value, open the test file instead
            self.update_message("Opening tests TSV...")
            self.test_manager._handle_open_test_file(e)
            self._add_to_db_button.color = None
        self.page.update()

    def _click_add_to_db(self, e: ft.ControlEvent):
        """Add the word to db, or update in db."""

        word_to_save = self.dpd_fields.get_current_headword()

        if (
            hasattr(self, "headword")
            and self.headword
            and hasattr(self, "headword_original")
            and self.headword_original
            and word_to_save.id
            == self.headword_original.id  # Compare ID from UI state with original
        ):
            committed, message = self._db.update_word_in_db(word_to_save)
            log_key = "pass2_update"  # It's an update if this block runs
        else:
            committed, message = self._db.add_word_to_db(word_to_save)
            log_key = "pass2_add"
            item_to_history = word_to_save

        if committed:
            request_dpd_server(str(word_to_save.id))
            item_id = (
                self.headword.id
                if hasattr(self, "headword") and self.headword
                else item_to_history.id
            )
            item_lemma = (
                self.headword.lemma_1
                if hasattr(self, "headword") and self.headword
                else item_to_history.lemma_1
            )

            if log_key == "pass2_add":
                item_id = item_to_history.id
                item_lemma = item_to_history.lemma_1
            else:
                item_id = self.headword.id
                item_lemma = self.headword.lemma_1

            was_new_to_history = self.history_manager.add_item(item_id, item_lemma)

            if was_new_to_history:
                self._daily_log.increment(log_key)

            if item_id is not None:
                removed_from_auto = self._pass2_auto_file_manager.remove_response(
                    str(item_id)
                )
                if removed_from_auto:
                    self.update_message(f"Removed ID {item_id} from pass2_auto.json")

            self._update_history_dropdown()
            self.page.update()
            self.clear_all_fields()
        else:
            self.update_message(f"Commit failed: {message}")

        self._add_to_db_button.color = ft.Colors.RED
        self.page.update()

    def _click_update_with_ai(self, e: ft.ControlEvent):
        """Handles the 'Update with AI' button click."""
        current_headword = self.dpd_fields.get_current_headword()
        if not current_headword or not current_headword.id:
            self.update_message("Load or create a headword first.")
            return

        self.update_message(f"Requesting AI update for {current_headword.lemma_1}...")

        # Call the controller's single-word processing method
        # Pass None for sentence_data for now
        response_dict = self.pass2_auto_controller.process_single_headword_from_view(
            current_headword
        )

        if response_dict:
            self.dpd_fields.update_add_fields(response_dict)
            self.update_message(
                f"AI suggestions loaded for {current_headword.lemma_1}."
            )
        else:
            self.update_message(f"AI update failed for {current_headword.lemma_1}.")

    def _click_delete_from_db(self, e: ft.ControlEvent):
        self.dpd_fields.clear_messages()

        if not self.headword:
            self.headword = self.dpd_fields.get_current_headword()

        self.delete_alert = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                controls=[
                    ft.Text("Delete Confirmation", color=ft.Colors.RED_900, size=20),
                    ft.Text("Are you sure you want to delete?"),
                    ft.Text(
                        str(self.headword.id),
                        color=ft.Colors.BLUE_200,
                        selectable=True,
                    ),
                    ft.Text(
                        self.headword.lemma_1,
                        color=ft.Colors.BLUE_200,
                        selectable=True,
                    ),
                ],
                height=150,
                width=500,
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            actions=[
                ft.TextButton("OK", on_click=self._click_delete_ok),
                ft.TextButton("Cancel", on_click=self._click_delete_cancel),
            ],
        )

        self.page.open(self.delete_alert)
        self.page.update()

    def _click_delete_ok(self, e: ft.ControlEvent):
        self.delete_alert.open = False
        self.page.update()

        if self.headword:
            deleted, message = self._db.delete_word_in_db(self.headword)
            if deleted:
                self.update_message(f"{self.headword.id} deleted from database")
            else:
                self.update_message(f"Delete failed: {message}")
            self.clear_all_fields()
        else:
            self.update_message("No headword to delete")

    def _click_delete_cancel(self, e: ft.ControlEvent):
        self.delete_alert.open = False
        self.page.update()

    def _click_backup_db(self, e: ft.ControlEvent):
        """Runs the backup script for DpdHeadword and DpdRoot tables."""
        # Instantiate ProjectPaths here
        pth = ProjectPaths()

        self.update_message("Running database backup...")

        try:
            # Call the function directly
            backup_dpd_headwords_and_roots(pth)
            self.update_message("Database backup completed successfully.")
            self.page.window.close()

        except Exception as ex:
            self.update_message(f"An unexpected error occurred during backup: {ex}")
            print(f"Backup error: {ex}")  # Log the error to console for debugging
