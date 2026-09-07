import sys
sys.path.append('c:/Users/Hp/Desktop/bookbot/backend')
from main import chat_about_document
import traceback

def main():
    try:
        print(chat_about_document('This is doc content', 'Hello', []))
    except Exception as e:
        with open('err.txt', 'w') as f:
            traceback.print_exc(file=f)

if __name__ == "__main__":
    main()
