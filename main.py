import flet as ft
import os
from groq import Groq

class ChatApp:
    def __init__(self):
        self.client = None
        self.chat_history = [{
            "role": "system",
            "content": "You are a helpful assistant. You reply with very short answers."
        }]

    def main(self, page: ft.Page):
        page.title = "Chat AI"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 20
        page.window_width = 400
        page.window_height = 600
        
        def check_api_key():
            stored_key = page.client_storage.get("groq_api_key")
            if stored_key:
                self.client = Groq(api_key=stored_key)
                show_chat()
            else:
                show_welcome()

        def save_api_key(e):
            api_key = api_key_field.value
            if api_key:
                page.client_storage.set("groq_api_key", api_key)
                self.client = Groq(api_key=api_key)
                show_chat()

        def show_welcome():
            page.clean()
            page.add(
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text("CHAT AI", size=32, weight=ft.FontWeight.BOLD),
                                    ft.Text("Powered by Groq", size=16, color=ft.colors.GREY_400),
                                ]
                            ),
                            margin=ft.margin.only(bottom=40)
                        ),
                        api_key_field,
                        ft.ElevatedButton(
                            text="Comenzar",
                            width=200,
                            on_click=save_api_key
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                )
            )

        def show_chat():
            page.clean()
            # Chat history display
            self.chat_display = ft.ListView(
                expand=True,
                spacing=10,
                auto_scroll=True,
                height=400
            )

            # Input field and send button
            self.input_field = ft.TextField(
                hint_text="Escribe tu mensaje...",
                border_radius=8,
                expand=True,
                on_submit=self.send_message
            )

            send_button = ft.IconButton(
                icon=ft.icons.SEND,
                on_click=self.send_message
            )

            # Layout
            page.add(
                ft.Container(
                    content=self.chat_display,
                    border=ft.border.all(1, ft.colors.OUTLINE),
                    border_radius=8,
                    padding=10,
                    expand=True
                ),
                ft.Row(
                    controls=[
                        self.input_field,
                        send_button
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
            )

        # API Key input field
        api_key_field = ft.TextField(
            label="Ingresa tu API Key de Groq",
            password=True,
            width=300,
            border_radius=8
        )

        # Check for stored API key on startup
        check_api_key()

    def create_message_bubble(self, message, is_user=True):
        return ft.Container(
            content=ft.Text(message),
            bgcolor=ft.colors.BLUE_700 if is_user else ft.colors.GREY_700,
            border_radius=8,
            padding=10,
            alignment=ft.alignment.center_right if is_user else ft.alignment.center_left,
        )

    def send_message(self, e):
        user_message = self.input_field.value
        if not user_message:
            return

        # Add user message to display
        self.chat_display.controls.append(
            self.create_message_bubble(user_message, True)
        )
        
        # Add to chat history
        self.chat_history.append({"role": "user", "content": user_message})
        
        try:
            # Get AI response
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=self.chat_history,
                temperature=1.2,
                max_tokens=2000,
                top_p=1
            )
            
            ai_message = response.choices[0].message.content
            
            # Add AI response to display
            self.chat_display.controls.append(
                self.create_message_bubble(ai_message, False)
            )
            
            # Add to chat history
            self.chat_history.append({"role": "assistant", "content": ai_message})
        except Exception as e:
            # Show error message if API call fails
            self.chat_display.controls.append(
                self.create_message_bubble(f"Error: {str(e)}", False)
            )
        
        # Clear input and update display
        self.input_field.value = ""
        self.chat_display.update()
        self.input_field.update()

if __name__ == "__main__":
    app = ChatApp()
    ft.app(target=app.main)