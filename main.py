from pathlib import Path
import random
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler
import yaml  # pyyaml


TOKEN = 'token'
AUTHORIZED_USERS = ['Verssania']


class Question:

    def __init__(self, qid, question, answers, note):
        self.qid = qid
        self.text = question
        self.answers = {}
        self.correct = None
        self.note = note
        for a in answers:
            aid = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[len(self.answers)]
            if isinstance(a, str):
                self.answers[aid] = a
            elif isinstance(a, dict) and len(a) == 1 and \
                    'correct' in a and self.correct is None:
                self.answers[aid] = a['correct']
                self.correct = aid
            else:
                raise ValueError(
                    f'Incorrect answers in question {qid}: {answers}')

QUESTIONS = {q['id']: Question(q['id'], q['q'], q['a'], q['n'])
    for q in yaml.full_load(Path('questions.yaml').read_text(encoding='utf-8'))}


def start(update, context):

    msg = update.message
    user = msg.from_user

    if 'username' not in context.user_data:
        context.user_data['username'] = user.username

    msg.bot.send_message(msg.chat_id,
        text=f'This quiz has been designed to give young people a quick and useful introduction to the European Union. Since its creation, the European Union has developed and expanded, with more and more countries joining forces to create a better future together. But how much do you know about the EU? Do you know what makes it unique and which countries are members, for example? Test yourself below and see whether you are an expert on the EU!')
    msg.bot.send_message(msg.chat_id,
        text=f'You will have {len(QUESTIONS)} questions',
        reply_markup=telegram.ReplyKeyboardMarkup([['Go']]))


def common_message(update, context):

    msg = update.message
    if 'quiz' not in context.user_data:
        context.user_data['quiz'] = {}
        context.user_data['quiz']['answers'] = {}
        context.user_data['quiz']['scores'] = 0


    else:
        answer = ""
        if msg.text == QUESTIONS[context.user_data['quiz']['current_qid']].correct:
            answer += "You're right!\n"
            context.user_data['quiz']['scores'] = context.user_data['quiz']['scores'] + 1
        else:
            answer += "You're wrong!\n"
            answer += f'Correct answer: {QUESTIONS[context.user_data["quiz"]["current_qid"]].correct} \n'
        notes = f'{QUESTIONS[context.user_data["quiz"]["current_qid"]].note}'
        msg.bot.send_message(msg.chat_id, text=f'{answer}')
        msg.bot.send_message(msg.chat_id, text=f'{notes}')
        # save response
        context.user_data['quiz']['answers'][context.user_data['quiz']['current_qid']] = msg.text

    # ask the question

    questions_left = set(QUESTIONS) - set(context.user_data['quiz']['answers'])

    if len(questions_left) > 0:

        question = QUESTIONS[random.sample(questions_left, 1)[0]]

        msg.bot.send_message(msg.chat_id, text=f'Question: {question.text}\n')
        msg.bot.send_message(msg.chat_id,
            text = 'Answer options:\n' + \
                '\n'.join(f'{aid}. {text}' for aid, text in sorted(question.answers.items())),
            reply_markup=telegram.ReplyKeyboardMarkup([[aid for aid in sorted(question.answers)]]))

        context.user_data['quiz']['current_qid'] = question.qid

    else:
        msg.bot.send_message(msg.chat_id, text=f'''Congratulations! Your score: {context.user_data['quiz']['scores']} / {len(QUESTIONS)}''')
        msg.bot.send_message(msg.chat_id,
            text= '''You've finished the "What is the European Union?" quiz.''')
        if context.user_data['quiz']['scores'] > (len(QUESTIONS)/2):
            msg.bot.send_message(msg.chat_id, 'Well done - you are truly an EU expert!',
            reply_markup=telegram.ReplyKeyboardRemove())
        else:
            msg.bot.send_message(msg.chat_id, 'You need to read more about the European Union.',
                                 reply_markup=telegram.ReplyKeyboardRemove())
        context.user_data['quiz']['current_qid'] = None


def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(None, common_message))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
