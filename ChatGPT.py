import json
import os
import uuid
from datetime import datetime

import requests


class ChatApp:
    """A class to interact with OpenAI's GPT models for chat applications."""

    def __init__(self, model="gpt-4", temperature=1, load_file=''):
        """
        Initializes the ChatApp with a specific model and optionally loads a chat history.

        :param model: The model to be used for chat completions, default is "gpt-4.0-turbo".
        :param load_file: Path to a file to load previous chat history, default is an empty string.
        """
        # The URL of the Flask app server which is running the API
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
        print(welcome_message)

        if load_file:
            if os.path.exists(load_file):
                load_confirm = input(
                    f"Do you want to load the previous chat history from '{load_file}'? (y/n): ").strip().lower()
                if load_confirm == 'y':
                    self.load(load_file)
                elif load_confirm == 'n':
                    print("Starting a new conversation.")
                else:
                    print("Invalid input. Starting a new conversation.")
            else:
                print(f"The file '{load_file}' does not exist. Starting a new conversation.")

    def _chat(self, message):
        """
        Handles a chat message, saves or exits if special commands are used.

        :param message: The message from the user.
        :return: The response from the model.
        """
        if message == "~exit":
            self.save()
            os._exit(1)
        elif message == "~save":
            self.save()
            return "(saved)"
        self.messages.append({"role": "user", "content": message})
        messages_payload = {
            "messages": self.messages,
            "temperature": self.temperature,
            "model": self.model,
        }
        response = requests.post(self.api_url, json=messages_payload)
        if response.status_code == 200:
            data = response.json()
            self.messages.append({"role": "assistant", "content": data['response']})
            return data['response']
        else:
            self.save()
            print(f"Failed to send request to {self.api_url}, save current conversation and exit!")
            os._exit(1)

    def chat(self):
        response = self._chat(input("USER: "))
        self.pretty_print_conversation(response, 'Assistant')

    def save(self):
        """Saves the chat history to a JSON file."""
        try:
            fn = self.get_file_name()
            print(f"Saving to 'history/{fn}'")
            with open(f"history/{fn}", "w", encoding='utf-8') as outfile:
                json.dump(self.messages, outfile, ensure_ascii=False, indent=4)
        except Exception:
            os._exit(1)

    @staticmethod
    def pretty_print_conversation(message, role):
        print("\n" + "-" * 50 + "\n")
        print(f"{role.upper()}: {message}\n\n" + "-" * 50 + "\n")

    def pretty_print_messages(self):
        for message in self.messages:
            print(f"Role: {message['role']}")
            content_lines = message['content'].split('\n')
            for line in content_lines:
                print(f"    {line}")
            print("\n" + "-" * 50 + "\n")  # Separator between messages

    def load(self, load_file):
        """Loads chat history from a file.

        :param load_file: Path to the file containing the chat history.
        """
        with open(load_file, "r", encoding='utf-8') as f:
            data = json.load(f)
            self.messages = data
        self.pretty_print_messages()

    def clear_chat(self):
        """Clears the chat history."""
        self.messages = []
        print("Chat history cleared.")

    def export_chat_to_txt(self, filename):
        """Exports the chat history to a text file.

        :param filename: The name of the text file to export to.
        """
        with open(filename, 'w') as file:
            for message in self.messages:
                role = message['role']
                content = message['content']
                file.write(f"{role}: {content}\n")
        print(f"Chat history exported to {filename}.")

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

    def set_model(self, model):
        """Sets the model used for chat completions.

        :param model: The model to be used.
        """
        self.model = model
        print(f"Model set to {model}.")

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
        response = requests.post(self.api_url, json=messages_payload)
        if response.status_code == 200:
            data = response.json()
            return formatted_now + data['response']
        else:
            return formatted_now + str(uuid.uuid4()) + ".json"

    def run(self):
        while True:
            self.chat()
