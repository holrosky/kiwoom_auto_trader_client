import telebot  # importing pyTelegramBotAPI library
import json
import threading
class TelegramMessage:
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        with open("config.json", "r", encoding="UTF8") as st_json:
            json_data = json.load(st_json)

        self.token = json_data['telegram_token']
        self.my_chat_id = json_data['telegram_chat_id']
        self.telegram_notification = True if json_data['telegram_notification'] == 'true' else False

        self.bot = telebot.TeleBot(self.token)

        # loop_thread = threading.Thread(target=self.main_loop)
        # loop_thread.start()
        #
        # @self.bot.message_handler(commands=['시작', '중지'])
        # def _msg_process(message):
        #     print(message.text[1:])
        #
        #     if '시작' in message.text:
        #         self.parent.start_trading()
        #         self.bot.send_message(chat_id=message.chat.id, text='자동매매를 시작합니다.')
        #     elif '중지' in message.text:
        #         self.parent.stop_trading()
        #         self.bot.send_message(chat_id=message.chat.id, text='자동매매를 중지합니다.')


    def extract_msg(self, message):
        print(message)

    def send_message(self, msg):
        try:
            if self.telegram_notification:
                self.bot.send_message(chat_id=self.my_chat_id, text=msg)
        except Exception as e:
            print(e)

    def main_loop(self):
        self.bot.polling(none_stop=True)
