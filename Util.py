__author__ = 'tianpengqi'
# -*- coding: utf-8 -*-

import base64
import hashlib
import ConfigParser
import redis
import requests
import ujson
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def sign(params, app_secret):
    params = sorted(params.iteritems(), key=lambda d: d[0])
    query_string = ''
    for eachParam, eachValue in params:
        if query_string == '':
            query_string += eachParam+'='+str(eachValue)
        else:
            query_string += '&'+eachParam+'='+str(eachValue)
    query_string += app_secret
    signature = hashlib.new('md5', query_string).hexdigest().upper()
    return signature


def parse_query_string(params):
    query_string = ''
    for each_key, each_value in params:
        if query_string == '':
            query_string += each_key+'='+str(each_value)
        else:
            query_string += '&'+each_key+'='+str(each_value)
    return query_string


def parse_query_string_of_dict(params):
    query_string = ''
    for each_key, each_value in params.items():
        if query_string == '':
            query_string += each_key+'='+str(each_value)
        else:
            query_string += '&'+each_key+'='+str(each_value)
    return query_string


def encode_pass(password):
    return base64.b64encode(
        hashlib.new(
            'sha1',
            'wealthbetter'+hashlib.new('sha1', password).hexdigest()
        ).hexdigest()
    )


def parse_config(path='config.conf'):
    config = ConfigParser.ConfigParser()
    config.read(path)
    return config


def get_redis():
    config = parse_config()
    redis_connection = redis.Redis(
        host=config.get('redis', 'host'),
        port=config.get('redis', 'port'),
        db=config.get('redis', 'db')
    )
    return redis_connection


def get_verify_code(mobile, request_type=1):
    config = parse_config()
    send_mobile_verify_params = {
        'mobile': mobile,
        'way': request_type
    }
    send_mobile_verify_params['authSign'] = sign(send_mobile_verify_params, config.get('interface', 'appSecret'))
    send_mobile_verify_url = config.get('interface', 'apiUrl')+'sendMobileVerify'
    mobile_verify = requests.post(send_mobile_verify_url, send_mobile_verify_params,verify=False).text
    print(mobile_verify)
    mobile_verify = ujson.loads(mobile_verify)
    if mobile_verify['msg'] == 'OK':
        mobile_code = mobile_verify['data']['mobile_code'].split('_')[-1]
        return mobile_code
    return False


def get_token():

    redis_connection = get_redis()
    user_info = redis_connection.get('USER_INFO')
    if user_info is None:
        return False
    user_info = ujson.loads(user_info)
    token = user_info['data']['token']
    return token


def login():
    config = parse_config()
    api_url = config.get('interface', 'apiUrl')
    redis_connection = get_redis()
    response = redis_connection.get('USER_INFO')
    if not response:
        muname = config.get('user', 'muname')
        mupass = encode_pass(config.get('user', 'mupass'))
        login_url = api_url+'login'
        headers = {'user-agent': 'Mozilla/5.0 (Linux; U; Android 2.3.6; zh-cn; GT-S5660 Build/GINGERBREAD) '
                                 'AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1 '
                                 'MicroMessenger/4.5.255'}
        r = requests.post(login_url, {'muname': muname, 'mupass': mupass}, verify=False, headers=headers)
        print(r.text)
        # r = get(login_url, {'muname': muname, 'mupass': mupass})
        response = r.text
        if r.status_code == 200 and response:
            response_obj = ujson.loads(response)
            if response_obj['error_code'] == 0:
                redis_connection.set('USER_INFO', response, ex=1800)
                return response_obj
            else:
                print(response_obj['msg'])
                return False
        else:
            print(response)


def get(url, params=None):
    if params is not None:
        url += '?'+parse_query_string_of_dict(params)
    r = requests.get(url, verify=False)
    if r.status_code != 200:
        print('Error '+str(r.status_code)+chr(10))
    else:
        print('Successfully Connected Address:'+url+'\n')
        print('The Response Data is :'+"\n\r")
        print(r.text+chr(10))
        print('The Parsed Data is :'+'\n\r')
        response = ujson.loads(r.text)
        print(response)
        return r


def post(url, params={}, files={}):
    #headers = {'user-agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0'}
    #headers = {'user-agent':'android-async-http/1.4.5 (http://loopj.com/android-async-http)'}
    #headers = {'user-agent': 'wealthbetter/1.2.5.1 (iPhone; iOS 7.1.1; Scale/2.00)'}
    headers = {'user-agent': 'Mozilla/5.0 (Linux; U; Android 2.3.6; zh-cn; GT-S5660 Build/GINGERBREAD) AppleWebKit/533.1'
                             ' (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1 MicroMessenger/4.5.255'}
    if not files:
        r = requests.post(url, data=params, verify=False, headers=headers)
    else:
        r = requests.post(url, data=params, files=files, verify=False, headers=headers)
    if r.status_code != 200:
        print('Error '+str(r.status_code)+chr(10)+str(r.text))
    else:
        print('Successfully Connected Address:'+url+'\n')
    print('The Response Data is :'+"\n\r")
    print(ujson.dumps(ujson.loads(r.text), ensure_ascii=False))
    print('The Parsed Data is :'+'\n\r')
    response = ujson.loads(r.text)
    string = var_dump(response)
    print(string)
    print(r.headers)


def var_dump(my_dict, level=1):
    my_type = type(my_dict)
    if my_type != dict and my_type != list and my_type != set and my_type != unicode and my_type != bool:
        return str(my_dict)+','
    elif my_type == unicode:
        return '"'+str(my_dict)+'",'
    elif my_type == dict:
        final_string = '['
        for k, v in my_dict.items():
            if type(k) == unicode:
                k = '"'+k+'"'
            final_string += '\n'+level*" "+k+' => '+var_dump(v, level+1+len(k))
        if level == 1:
            return final_string+'\n'+level*" "+'];'
        else:
            return final_string+'\n'+level*" "+'],'

    elif my_type == bool:
        return str(my_dict).lower()+','
    else:
        final_string = '[\n'
        for item in my_dict:
            final_string += level*" "+var_dump(item, level+1)+'\n'
        if level == 1:
            return final_string+'\n'+level*" "+'];'
        else:
            return final_string+'\n'+level*" "+'],'


def ping(url):
    r = requests.get(url, verify=False)
    print(r.status_code)


def fetch(url, params={}):
    if params is not None:
        r = requests.post(url, params, verify=False)
    else:
        r = requests.get(url, verify=False)
    if r.status_code != 200:
        print('Error NO.'+r.status_code)
    else:
        print(r.text)
