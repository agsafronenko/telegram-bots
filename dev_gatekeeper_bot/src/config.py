# Duration (in seconds) a new user has to answer the verification question
# Before being permanently banned from the chat
TIMEOUT_SECONDS = 60

# Short delay (in seconds) before deleting verification-related messages
# Helps prevent message flooding and provides brief visibility
DELAY = 2

# Generates personalized welcome message for new chat members
# Includes their username and a random coding challenge
def send_welcome_msg(user, question) -> str:
    return (
            f"Welcome <b>{user}</b>! To verify you're a programmer, please answer this question within <b>{TIMEOUT_SECONDS} seconds</b>:\n\n"
            f"{question}\n\n"
            f"Just send your answer as a reply."
        )

# Generates success message when a user passes the verification
def send_success_msg(user) -> str:
    return f"Congratulations! <b>{user}</b> passed the verification and can now participate in the chat."

# Generates failure message when a user fails the verification
def send_fail_msg(user) -> str:
    return f"<b>{user}</b> failed the verification, has been permanently banned from the chat, and all their messages have been deleted."

# Generates timeout message when a user doesn't respond in time
def send_timeout_msg(user) -> str:
    return f"User <b>{user}</b> didn't answer the verification question in time, and has been permanently banned from the chat"


# Collection of coding questions used for verifying new chat members
# Each question is a dictionary with 'question' and 'answer' keys
# Designed to test basic programming knowledge (Python and JavaScript)
CODING_QUESTIONS = [
    {"question": "What is the output of this Python code?\nb = ['a', 'b', 'c', 4]\nprint(b[2])", "answer": "c"},
    {"question": "What is the output of this code?\nx = 5\ny = 2\nprint(x % y)", "answer": "1"},
    {"question": "What does this JavaScript code return?\nlet arr = [10, 20, 30]; console.log(arr[1]);", "answer": "20"},
    {"question": "In Python, what's the result of 'Hello'[1]?", "answer": "e"},
    {"question": "What's the output of this code?\nprint(len('programming'))", "answer": "11"},
    {"question": "What will this JavaScript code output (ignore case)?\nconsole.log(typeof 42);", "answer": "number"},
    {"question": "Which keyword is used to define a function in Python?", "answer": "def"},
    {"question": "What does this JavaScript code return?\nconsole.log('5' + 3);", "answer": "53"},
    {"question": "What will this Python code output?\na = [1, 2, 3]\nprint(a[-1])", "answer": "3"},
    {"question": "Which symbol is used for single-line comments in Python?", "answer": "#"},
    {"question": "What will this JavaScript code output?\nconsole.log(10 == '10');", "answer": "true"},
    {"question": "What is the result of this Python expression (ignore case)?\nprint(bool(0))", "answer": "False"}
]
