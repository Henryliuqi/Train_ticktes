"""Train tickets query from CLI.
Usage:
    tickets [-dgktz] <from> <to> <date>
Options:
    -h --help     Show this screen.
    -d            动车
    -g            高铁
    -k            快速
    -t            特快
    -z            直达
"""
import requests
import stations
import argparse
from datetime import datetime
from prettytable import PrettyTable
from colorama import Fore
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class TrainCollection(object):

    headers = '车次 车站 时间 历时 一等座 二等座 软卧 硬卧 软座 硬座 无座'.split()

    def __init__(self, raw_trains, options):
        self.raw_trains = raw_trains
        self.options = options

    def colored(self, color, string):
        return ''.join([getattr(Fore, color.upper()), string, Fore.RESET])

    def get_from_to_station_name(self, data_list):
        from_station_telecode = data_list[6]
        to_station_telecode = data_list[7]
        return '\n'.join([
            self.colored('green', stations.get_name(from_station_telecode)),
            self.colored('red', stations.get_name(to_station_telecode))
        ])

    def get_start_arrive_time(self, data_list):
        return '\n'.join([
            self.colored('green', data_list[8]),
            self.colored('red', data_list[9])
        ])

    def parse_train_data(self, data_list):
        return {
            'station_train_code': data_list[3],
            'from_to_station_name': self.get_from_to_station_name(data_list),
            'start_arrive_time': self.get_start_arrive_time(data_list),
            'lishi': data_list[10],
            'first_class_seat': data_list[31] or '--',
            'second_class_seat': data_list[30] or '--',
            'soft_sleep': data_list[23] or '--',
            'hard_sleep': data_list[28] or '--',
            'soft_seat': data_list[24] or '--',
            'hard_seat': data_list[29] or '--',
            'no_seat': data_list[33] or '--'
        }

    def need_print(self, data_list):
        station_train_code = data_list[3]
        initial = station_train_code[0].lower()
        return (not self.options or initial in self.options)

    @property
    def trains(self):
        for train in self.raw_trains:
            data_list = train.split('|')
            if self.need_print(data_list):
                yield self.parse_train_data(data_list).values()

    def pretty_print(self):
        pt = PrettyTable()
        pt._set_field_names(self.headers)
        for train in self.trains:
            pt.add_row(train)
        print(pt)


class Cli(object):

    def __init__(self):
        super(Cli, self).__init__()

    def check_arguments_validity(self, date, from_station, to_station):
        if from_station is None or to_station is None:
            print(u'请输入有效的车站名称')
            exit()
        try:
            if datetime.strptime(date, '%Y-%m-%d') < datetime.now():
                raise ValueError
        except:
            print(u'请输入有效日期')
            exit()

    def start(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', action='append', dest='option', default=['g','d'], help='...')
        parser.add_argument('-f', action='store', type=str, dest='form', default='', help='...')
        parser.add_argument('-t', action='store',type=str, dest='to', default='', help='...')
        parser.add_argument('-T', action='store', dest='time', default='', help='...')
        self.pas = parser.parse_args()
        self.run()

    def run(self):
        url_template = (
            'https://kyfw.12306.cn/otn/leftTicket/queryO?leftTicketDTO.'
            'train_date={}&'
            'leftTicketDTO.from_station={}&'
            'leftTicketDTO.to_station={}&'
            'purpose_codes=ADULT'
        )
        from_station = stations.get_telecode(self.pas.form)
        to_station = stations.get_telecode(self.pas.to)
        date = self.pas.time
        self.check_arguments_validity(date, from_station, to_station)
        url = url_template.format(date, from_station, to_station)
        r = requests.get(url)
        r.encoding = 'utf-8'
        trains = r.json()['data']['result']
        TrainCollection(trains, self.pas.option).pretty_print()


if __name__ == '__main__':
    Cli().start()