from ChatGPT import ChatApp

app = ChatApp(model="gpt-4", load_file='')


def main():
    while True:
        app.chat()


if __name__ == "__main__":
    main()
