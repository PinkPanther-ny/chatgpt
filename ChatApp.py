import json
import os
import sys
import threading
import tkinter as tk
import uuid
from datetime import datetime
from tkinter import Scale, Frame, Label, Button, END
from tkinter import filedialog

import requests
from PIL import ImageTk, Image


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # noqa
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ChatApp:
    """A class to interact with OpenAI's GPT models for chat applications."""

    def __init__(self, model="gpt-4", temperature=1, load_file=''):
        """
        Initializes the ChatApp with a specific model and optionally loads a chat history.

        :param model: The model to be used for chat completions, default is "gpt-4.0-turbo".
        :param temperature: The temperature to use for the chat completions.
        :param load_file: Path to a file to load previous chat history, default is an empty string.
        """
        self.api_url = 'http://openai.fxpyramid.com/interact/'
        self.model = model
        self.temperature = temperature
        self.messages = []
        welcome_message = """
        Welcome to ChatApp!

        Here's how to get started:

        1. Starting a Chat:
           - Simply type your message and hit Enter to send it.

        2. Saving Your Chat:
           - At any point, if you wish to save the current chat, type `~save` and press Enter. You'll see the message "(saved)" confirming that your conversation is safely stored.

        3. Exiting the App:
           - When you are ready to end your session, type `~exit` and press Enter. This will save your chat history and close the application.

        Enjoy your conversation!

        """
        self.root = tk.Tk()
        self.root.title("ChatApp")
        ico = ImageTk.PhotoImage(Image.open(resource_path('./chatapp.ico')))
        self.root.iconphoto(False, ico)  # noqa
        # Initialize the total cost to zero
        self.total_cost = 0

        # Set up grid weights for resizing
        self.root.grid_columnconfigure(0, weight=1)
        # Set up grid weights for resizing
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(4, weight=1)  # This should be the chat_frame's row

        # Other rows should have a weight of 0 or be omitted if they shouldn't resize vertically
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_rowconfigure(3, weight=0)
        self.root.grid_rowconfigure(5, weight=0)
        self.root.grid_rowconfigure(6, weight=0)

        # Cost Display Label
        self.cost_label = Label(self.root, text=f"Total Cost: {self.total_cost}")
        self.cost_label.grid(row=0, column=0, sticky="ew")

        # History Frame
        history_frame = Frame(self.root)
        history_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        history_label = Label(history_frame, text="Select History File:")
        history_label.grid(row=0, column=0, sticky="w")

        history_btn = Button(history_frame, text="Browse", command=self.load_history)
        history_btn.grid(row=0, column=1, sticky="e")

        # Model Frame
        model_frame = Frame(self.root)
        model_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        model_label = Label(model_frame, text="Select Model:")
        model_label.grid(row=0, column=0, sticky="w")

        self.model_var = tk.StringVar(self.root)
        self.model_var.set(self.model)  # default value

        model_option = tk.OptionMenu(model_frame, self.model_var, "gpt-4", "gpt-3.5-turbo")
        model_option.grid(row=0, column=1, sticky="e")

        # Temperature Slider
        self.temperature_scale = Scale(self.root, from_=0, to=2, resolution=0.01, orient="horizontal",
                                       label="Temperature")
        self.temperature_scale.set(self.temperature)
        self.temperature_scale.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

        # Chat Frame
        chat_frame = Frame(self.root)
        chat_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        chat_frame.grid_columnconfigure(0, weight=1)
        chat_frame.grid_rowconfigure(0, weight=1)

        self.chat_history = tk.Text(chat_frame, width=80, height=20, wrap="word")
        self.chat_history.grid(row=0, column=0, sticky="nsew")
        self.chat_history.config(state="disabled")

        scrollbar = tk.Scrollbar(chat_frame, command=self.chat_history.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_history['yscrollcommand'] = scrollbar.set

        # User Input
        self.user_input = tk.Entry(self.root)
        self.user_input.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        self.user_input.bind("<Return>", self.send_message)

        # Button Frame
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=5)
        button_frame.grid_columnconfigure(1, weight=1)  # This will push the send button to the right

        # Prepare Button (remains unchanged on the left)
        self.prepare_button = tk.Button(button_frame, text="Prepare", command=self.prepare_message, width=7)
        self.prepare_button.grid(row=0, column=1, padx=5, sticky="w")  # Aligns to the left

        # Role Selection Frame (remains unchanged next to the prepare button)
        role_frame = tk.Frame(button_frame)
        role_frame.grid(row=0, column=0, sticky="w",
                        padx=5)  # Aligns to the left, in the same column as the prepare button

        role_label = tk.Label(role_frame, text="Select Role:")
        role_label.grid(row=0, column=0, sticky="w")

        self.role_var = tk.StringVar(self.root)
        self.role_var.set("user")  # default value

        role_option = tk.OptionMenu(role_frame, self.role_var, "user", "system")
        role_option.grid(row=0, column=1, sticky="w")

        # Send Button (move to the right side)
        self.send_button = tk.Button(button_frame, text="Send", command=self.send_message, width=7)
        self.send_button.grid(row=0, column=1, sticky="e")  # Now aligns to the right due to column weight

        self.update_chat_history(welcome_message, "Program")

    def save(self):
        """Saves the chat history to a JSON file."""
        try:
            fn = self.get_file_name()
            print(f"Saving to 'history/{fn}'")
            self.update_chat_history(f"Saving to 'history/{fn}'", "Program")
            with open(f"history/{fn}", "w", encoding='utf-8') as outfile:
                json.dump(self.messages, outfile, ensure_ascii=False, indent=4)
        except Exception:
            os._exit(1)

    def load(self, load_file):
        """Loads chat history from a file.

        :param load_file: Path to the file containing the chat history.
        """
        with open(load_file, "r", encoding='utf-8') as f:
            data = json.load(f)
            self.messages = data

        self.chat_history.delete('1.0', END)
        for message in self.messages:
            role = message['role'].upper()
            content = message['content']
            self.update_chat_history(content, role)

    def get_chat_history(self):
        """Returns the chat history as a formatted string.

        :return: A string representing the chat history.
        """
        history = ""
        for message in self.messages:
            role = message['role']
            content = message['content']
            history += f"{role}: {content}\n"
        return history

    def get_file_name(self):
        # Format the date and time to 'YYYY_MM_DD_HH_MM'
        formatted_now = datetime.now().strftime('%Y_%m_%d_%H_%M_')
        system_prompt = [{"role": "system",
                          "content": "You are a filename generator, based on current conversation, generate a valid "
                                     "file name with suffix .json, you must return the filename directly without "
                                     "output anything else, this is an automated program."}]

        messages_payload = {
            "messages": self.messages + system_prompt,
            "temperature": self.temperature,
            "model": self.model,
        }
        response = requests.post(self.api_url, json=messages_payload, timeout=300)
        if response.status_code == 200:
            data = response.json()
            return formatted_now + data['response']
        else:
            return formatted_now + str(uuid.uuid4()) + ".json"

    def run(self):
        self.root.mainloop()

    def prepare_message(self):
        message = self.user_input.get()
        role = self.role_var.get()
        if message:
            self.user_input.delete(0, END)
            # Just append the message with the selected role and update the GUI
            self.messages.append({"role": role, "content": message})
            self.update_chat_history(message, role)

    def send_message(self, event=None):
        message = self.user_input.get()
        role = self.role_var.get()

        self.user_input.delete(0, END)
        # Disable user input and buttons while processing
        self.disable_input_widgets()
        threading.Thread(target=self.process_message, args=(message, role)).start()

    def process_message(self, message, role):
        """
        Processes a chat message, including special commands and normal chat.

        :param message: The message from the user.
        :param role: The role of the message sender.
        """
        # Handle special commands first
        try:
            if message == "~exit":
                self.save()
                os._exit(1)
            elif message == "~save":
                self.save()
                return

            # Add message to the history
            if message:
                self.messages.append({"role": role, "content": message})
                self.update_chat_history(message, role)  # Update the chat history in the GUI with the user's message

            # Normal message handling, send the payload to the API and get the response
            messages_payload = {
                "messages": self.messages,
                "temperature": self.temperature,
                "model": self.model,
            }
            response = requests.post(self.api_url, json=messages_payload, timeout=300)
            if response.status_code == 200:
                data = response.json()
                # Extract the cost from the response and add it to the total cost
                cost = data.get('cost', 0)  # Ensure there is a default of 0 if 'cost' is not in the response
                self.total_cost += cost

                # Update the cost display label
                self.cost_label.config(text=f"Total Cost: {self.total_cost:.5f} $")

                # Append the assistant's response to the messages list
                self.messages.append({"role": "assistant", "content": data['response']})
                # Update the chat history in the GUI with the assistant's response
                self.update_chat_history(data['response'], 'Assistant')
            else:
                # Handle the error case as before
                self.update_chat_history(f"Failed to get a response, status code: {response.status_code}",
                                         'Program')
        except Exception as e:
            self.update_chat_history(f"Failed to get a response, exception: {str(e)}",
                                     'Program')
        finally:
            # Re-enable user input and buttons after processing
            self.enable_input_widgets()

    def disable_input_widgets(self):
        """Disables input widgets to prevent user interaction."""
        self.user_input.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.prepare_button.config(state=tk.DISABLED)

    def enable_input_widgets(self):
        """Enables input widgets to allow user interaction."""
        self.user_input.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
        self.prepare_button.config(state=tk.NORMAL)

    def load_history(self):
        history_path = filedialog.askopenfilename(initialdir="./history", title="Select file",
                                                  filetypes=(("json files", "*.json"), ("all files", "*.*")))
        if history_path:
            self.load(history_path)

    def update_chat_history(self, message, role):
        if self.chat_history.winfo_exists():
            self.chat_history.config(state=tk.NORMAL)
            self.chat_history.insert(END, f"{role.upper()}: {message}\n\n ------ \n\n ")
            self.chat_history.yview(END)
            self.chat_history.config(state=tk.DISABLED)


if __name__ == "__main__":
    ChatApp(model="gpt-4", load_file='').run()
