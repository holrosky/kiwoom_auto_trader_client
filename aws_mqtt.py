import threading
from collections import OrderedDict

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import time
import argparse
import json
import glob

class AWS_mqtt():
    def __init__(self, parent):
        self.parent = parent


        certificatePath = ""
        privateKeyPath = ""
        host = ""



        path = "certificates/*.crt"
        certificatePath = glob.glob(path)[0]

        path = "certificates/*private.pem.key"
        privateKeyPath = glob.glob(path)[0]

        with open("config.json", "r", encoding="UTF8") as st_json:
            json_data = json.load(st_json)

        sCode = json_data['sCode']
        host = json_data['host']
        is_test_mode = json_data['test_mode']

        clientId = json_data['client_id']

        if is_test_mode == 'yes':
            clientId = clientId + '/test'

        else:
            clientId = clientId + '/real'

        self.subscribe_topic = sCode + '/' + clientId + '/#'
        self.publish_topic = sCode + '/' + clientId + '/auto_trader'


        rootCAPath = "certificates/root.pem"

        port = 8883

        self.myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
        self.myAWSIoTMQTTClient.configureEndpoint(host, port)
        self.myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)


        # AWSIoTMQTTClient connection configuration
        self.myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
        self.myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        self.myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
        self.myAWSIoTMQTTClient.configureConnectDisconnectTimeout(2)  # 10 sec
        self.myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

        # Connect and subscribe to AWS IoT
        self.myAWSIoTMQTTClient.connect()
        self.myAWSIoTMQTTClient.subscribe(self.subscribe_topic, 0, self.customCallback)



    def customCallback(self, client, userdata, message):
        try:
            message_string = message.payload

            if message_string[0] == 'b':

                message_string = message_string[1:]
            if message_string[0] == "'":
                message_string = message_string[1:len(message_string)-1]

            message_to_json = json.loads(message_string)

            if message_to_json['command'] == 'running_state_require':
                temp = {}
                temp['command'] = 'running_state'
                self.publish_message(temp)

            elif message_to_json['command'] == 'json_state_require_from_android':
                with open("setting.json", "r", encoding="UTF8") as st_json:
                    json_data = json.load(st_json)
                    json_data['command'] = 'json_state_from_auto_trader'
                    self.publish_message(json_data)

            elif message_to_json['command'] == 'json_update_require_from_android':
                print('update')
                del (message_to_json['command'])

                with open('setting.json', 'w', encoding="UTF8") as f:
                    json.dump(message_to_json, f, ensure_ascii=False, indent=4)

                message_to_json['command'] = 'json_update_from_auto_trader'
                self.publish_message(message_to_json)

                while self.parent.load_needed:
                    time.sleep(0.1)
                self.parent.is_load_needed(True)

            elif message_to_json['command'] == 'clear_position_require_from_android':
                self.parent.clear_position_from_user(int(message_to_json['position']))

            elif message_to_json['command'] == 'remove_strategy_from_android':
                self.parent.remove_strategy(int(message_to_json['position']))

            elif message_to_json['command'] == 'add_strategy_from_android':
                self.parent.add_strategy()

            elif message_to_json['command'] == 'get_profit_from_android':
                day_profit_info = self.parent.get_day_profit(message_to_json['acc_num'], message_to_json['time'])

                temp = {}

                temp['command'] = 'profit_from_auto_trader'

                if day_profit_info == 0:
                    temp['trade_profit'] = '0'
                    temp['fee'] = '0'
                    temp['total_profit'] = '0'
                else:
                    temp['trade_profit'] = day_profit_info['청산손익']
                    temp['fee'] = day_profit_info['수수료']
                    temp['total_profit'] = day_profit_info['실손익']

                self.publish_message(temp)

            elif message_to_json['command'] == 'print_chart_data':

                self.parent.print_chart_data(message_to_json)

            elif message_to_json['command'] == 'length_require_from_android':
                temp = {}
                temp['command'] = 'length_from_auto_trader'
                temp['queue_length'] = str(len(self.parent.real_data_queue))
                temp['calc_indicators_length'] = str(self.parent.num_of_calc_indicator)

                self.publish_message(temp)
        except Exception as e:
            print(e)

    def publish_message(self, message):
        try:
            messageJson = json.dumps(message)
            self.myAWSIoTMQTTClient.publish(self.publish_topic , messageJson, 0)
        except Exception as e:
            print(e)


    def disconnect(self):
        try:
            self.myAWSIoTMQTTClient.disconnect()
        except Exception as e:
            print(e)
