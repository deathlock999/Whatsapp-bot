from celery import Celery
from celery.schedules import crontab

app = Celery('tasks', broker='redis://redis:6379/0')  # Adjust if using a different service name or port
api_token = "fGQJvjbzsCUPB7QtImHL8okh7QEPnpzm"

url = "https://gate.whapi.cloud/messages/poll"

group_id = "120363261013619385@g.us"


sheet_id = "1ddIhjrBUJaA7Rc0oZTzc4wf1Tn6_ABn-fB8GTZD4YNQ"
worksheet_name = "Sheet1"
answers = []
correct_ans_set = []

@app.task
def run_bot():
    for z in range(1,5):
        last_question_index = update_index_file()
        print(last_question_index)
        data=get_data_from_sheets(sheet_id, worksheet_name, last_question_index)
        if data:
            question = data["question"]
            answers = data["answers"]
            correct_answer = data["correct_answer"]
            send_poll(question, answers)
            #correct answer...
            correct_ans_set.append(correct_answer)
            answers.clear()
            time.sleep(1800) 
    send_message(api_token, group_id, correct_ans_set)              
    correct_ans_set.clear() 
    time.sleep(1800)     
    print("...one circle...")
    

    return "Bot execution complete!"  # Optional return value for monitoring

def update_index_file():
  try:
    with open("file.txt", 'r+') as f:
      # Handle empty file case (initialize to 0)
      content = f.read()
      last_index_id = int(content.strip()) if content else 0

      # Increment and update the file
      last_index_id += 1
      f.seek(0)
      f.write(str(last_index_id))

      # Return the updated last index ID
      return last_index_id
  except FileNotFoundError:
    # Handle case where the file doesn't exist (create it with initial value 0)
    with open("file.txt", 'w') as f:
      f.write('0')
      return 0

def translate(to_translate):
    translated = GoogleTranslator(source='auto', target='si').translate(to_translate)
    return translated

def get_data_from_sheets(sheet_id, worksheet_name, last_question_index, source_language='en', target_language='si'):

    try:
        gc = gspread.service_account(filename="luca-420106-ab9a1b42fc61.json")  # Replace with your credentials file path
        worksheet = gc.open_by_key(sheet_id).worksheet(worksheet_name)

        question = worksheet.cell(last_question_index, 1).value
        if not question:
            print(f"Empty row encountered at index {last_question_index}. Skipping...")
            return None

        answers = []
        all_answers_filled = True  # Flag to track if all answers are filled

        for i in range(2, 6):
            if (len(answers) < 4):
                answer = worksheet.cell(last_question_index, i).value
                # Append answer only if it has a value (not empty)
                if answer:
                    answers.append(answer)
                # If an empty answer is found, set the flag and break the loop
                else:
                    all_answers_filled = False
                    break

        # Skip processing this row if any answer is empty
        if not all_answers_filled:
            print(f"Row {last_question_index} skipped due to empty answer(s).")
            return None

        correct_answer = worksheet.cell(last_question_index, 6).value
        translator = GoogleTranslator(source=source_language, target=target_language)

        translated_question = translator.translate(question)
        translated_answers = [translator.translate(answer) for answer in answers]
        translated_correct_answer = translator.translate(correct_answer)

        return {
            "question": translated_question,
            "answers": translated_answers,
            "correct_answer": translated_correct_answer
        }

    except Exception as e:
        print(f"Error retrieving data from Google Sheet: {e}")
        return None 


def send_poll(question,answers):
    payload = {
        "to": '120363261013619385@g.us',
        "options": answers,
        "title": question,
        "count": 1,
        "ephemeral": 10
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": api_token
    }
    response = requests.post(url, json=payload, headers=headers)

    print(response.text)

def send_message(api_token, group_id, correct_ans_set):
    """
    Sends a message containing the correct answers to the specified WhatsApp group.

    Args:
        api_token (str): Your WhatsApp API token.
        group_id (str): ID of the WhatsApp group.
        correct_ans_set (list): List of correct answers.

    Returns:
        dict (or None): Response dictionary from the API call, or None if an error occurs.
    """
    print(f"Correct answers: {correct_ans_set}")

    base_url = "https://gate.whapi.cloud/"
    endpoint = "messages/text"

    # Build the message dynamically based on the number of correct answers
    message = f"**නිවැරදි පිළිතුරු**\n"
    for i, answer in enumerate(correct_ans_set):
        message += f"{i+1}. {answer}\n"

    correct_ans_set.clear()  # Clear the list for future use

    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    data = {
        "to": group_id,
        "body": message
    }

    try:
        response = requests.post(url=f"{base_url}{endpoint}", headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return response.json()  # Return the JSON response if successful
        print("Sent")
    except requests.exceptions.RequestException as error:
        print(f"Error sending message: {error}")
        return None  # Indicate an error


# **Configure periodic task with djcelery**
from djcelery.schedulers import Scheduler

sched = Scheduler(app=app)

@sched.schedule(crontab(minute='*/30'))  # Run every 30 minutes
def run_bot_periodic():
    run_bot.delay()  # Delay task execution for efficiency

sched.install()
