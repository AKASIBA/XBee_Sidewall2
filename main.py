# 巻上げ制御
import binascii
import xbee
import machine
import uio
import os
import time
from machine import Pin

ON = 5
OFF = 4
addr_coordinator = '\x00\x00\x00\x00\x00\x00\x00\x00'
xbee.atcmd('ID', 0x480)  # pan_id 480
xbee.atcmd('AV', 0x00)  # ADC_reference_1.25V
temp = machine.ADC('D1')
manual_sw = Pin('D10', mode=Pin.IN, pull=Pin.PULL_UP)
open_sw = Pin('D8', mode=Pin.IN, pull=Pin.PULL_UP)
close_sw = Pin('D11', mode=Pin.IN, pull=Pin.PULL_UP)
sl = str(binascii.hexlify(xbee.atcmd('SL')))[6:-1]
print(sl)
drv = ["""&{'temp':'25','o_time':'07:00','c_time':'16:00','select':'21','wall':'21','everyday':'10',\
'remote':'10','button':'01'}""", """<body><h1><strong>くるファミ　AceDX</strong></h1><form name="Form" method="POST">\
<input name="cont_dev" value='""" + sl + """' hidden>""", """<p><input type="radio" id="select1" name="select" \
value='21' &> 手動<input type="radio" id="select2" name="select"  value='22' &> 自動</p>""",
       """<p><button class="button" name="button" value='02' type="submit" id="button"><strong>開</strong></button>""",
       """<button class="button" name="button" value='03' type="submit" id="button"><strong>閉</strong></button>\
 <button class="button" name="button" value='04' type="submit" id="button"><strong>停止</strong></button></p>""",
       """<input type="radio" name="wall" value="21" &>\
温度制御<input type="radio" name="wall" value="22" &> 時間制御</p>""",
       """<p>設定温度<input type="number" id="text" name="temp" value= $ min="0" max="35"> ℃</p>""", """<p>\
       <label>開く時刻  : <input type="time" id='time' name='o_time' value= $ required></p>\
<p><label>閉る時刻  : <input type="time" id='time' name='c_time' value= $ required></p>""",
       """<p><label>毎日同時刻に実行 :<input type="checkbox" name="everyday" id="text" value='11' &></label></p>""", """<p>\
       <label>リモート操作有効 :<input type="checkbox" name="remote" id="text" value='11' &></label></p>\
<p><button class="button" name="button" value='01' type="submit" id="button"><strong>実行</strong></button>""",
       """<button class="button" name="control" value='CANCEL' type="submit" id="button"><strong>戻る\
</strong></button></p></body></html>""", '?',
       """>if 'temp' in form:exe_dict['temp'] = '{:0>2}'.format(form.getvalue('temp'))@@""",
       """>if 'o_time' in form:exe_dict['o_time'] = '{:0>2}'.format(form.getvalue('o_time'))@@\
if 'c_time' in form:exe_dict['c_time'] = '{:0>2}'.format(form.getvalue('c_time'))@@""",
       """>exe_dict['select'] = '{:0>2}'.format(form.getvalue('select')) if form.getvalue('select') else '21'@@\
exe_dict['wall'] = '{:0>2}'.format(form.getvalue('wall')) if form.getvalue('wall') else '21'@@""",
       """>exe_dict['everyday'] = '{:0>2}'.format(form.getvalue('everyday'))if form.getvalue('everyday')else '10' @@""",
       """>exe_dict['remote'] = '{:0>2}'.format(form.getvalue('remote')) if form.getvalue('remote') else '10'@@""",
       """>if 'button' in form:exe_dict['button'] = '{:0>2}'.format(form.getvalue('button'))@@""", '@']


def xb_join():
    while True:
        status = xbee.atcmd('AI')  # network_join
        print('.', end='')
        if status == 0x00:
            print('\nJoin!')
            break
        xbee.atcmd('CB', 0x01)  # commissioning_1
        time.sleep(2)


def pin_ini():
    xbee.atcmd('d2', OFF)
    xbee.atcmd('d3', OFF)
    xbee.atcmd('d6', OFF)


def packet_receive():
    payload = ''
    packet = xbee.receive()
    if packet:
        payload = str(packet['payload'].decode('utf-8'))
    return payload


def send_driver():
    print('install_command')
    for i in drv:
        print(i)
        xbee.transmit(addr_coordinator, i)
        time.sleep_ms(100)
    print('send!')


def main():
    pin_ini()
    now_time = s_time = p_time = 0
    temp_c = o_time = c_time = select = ''
    wall = everyday = remote = button = ''
    d = p = True
    t0 = 0
    mes_c = 'C0100001リモート　OFF'
    conf = ''
    c = True
    t_w = False
    w_s = True
    o = True
    time_w = k_time = off_time = 0
    so_time = sc_time = ''
    manual = False
    m_s = True
    time_calibration = True
    m = 0
    try:
        f = uio.open('conf.txt', mode='r')
        conf = f.read()
        f.close()
    except OSError:
        print('設定ファイルがありません')
    xbee.transmit(addr_coordinator, 'S')
    while True:
        t = time.ticks_ms()
        if t0 <= t or t0 - t >= 3000:  #
            t0 = t + 1000
            if now_time >= 86400:
                now_time = 0
                p_time = 0
                time_calibration = True
            now_time = now_time + 1
            s_time = int(now_time / 60)
        command = packet_receive()
        if c:
            command = conf
            c = False
        if command:
            print(command)
            if command == 'sibainu':
                send_driver()
            if command[0:2] == '99':
                now_time = int(command[-6:])
                s_time = int(now_time / 60)
            else:
                manual = False
                xbee.atcmd('d4', OFF)
                try:
                    now_time = int(command[-6:])
                    s_time = int(now_time / 60)
                    temp_c = int(command[0:2])
                    o_time = int(command[2:4]) * 60 + int(command[5:7])
                    c_time = int(command[7:9]) * 60 + int(command[10:12])
                    select = command[12:14]
                    wall = command[14:16]
                    everyday = command[16:18]
                    remote = command[18:20]
                    button = command[20:22]
                    so_time = command[2:7]
                    sc_time = command[7:12]
                    d = True
                    try:
                        os.remove('conf.txt')
                        f = uio.open('conf.txt', mode='w')
                        f.write(command)
                        f.close()
                    except OSError:
                        pass

                except SyntaxError:
                    temp_c = int(conf[0:2])
                    o_time = int(conf[2:4]) * 60 + int(conf[5:7])
                    c_time = int(conf[7:9]) * 60 + int(conf[10:12])
                    select = conf[12:14]
                    wall = conf[14:16]
                    everyday = conf[16:18]
                    remote = conf[18:20]
                    button = conf[20:22]
                    so_time = command[2:7]
                    sc_time = command[7:12]
            if remote == '11':
                xbee.atcmd('d6', ON)
                mes_c = 'C0100001リモート　ON'
                if select == '21':  # 手動
                    xbee.atcmd('d7', OFF)
                    xbee.atcmd('d9', OFF)
                    if button == '02':
                        xbee.atcmd('d3', OFF)
                        xbee.atcmd('d2', ON)
                        print('OPEN')
                    if button == '03':
                        xbee.atcmd('d2', OFF)
                        xbee.atcmd('d3', ON)
                        print('CLOSE')
                    if button == '04':
                        xbee.atcmd('d2', OFF)
                        xbee.atcmd('d3', OFF)
                        print('OFF')
                if select == '22':
                    if wall == '21':
                        xbee.atcmd('d9', OFF)
                        xbee.atcmd('d7', ON)
                        mes_c = "C0100001巻上温度:" + str(temp_c) + '℃'
                    if wall == '22' and (d or everyday == '11'):
                        xbee.atcmd('d7', OFF)
                        xbee.atcmd('d9', ON)
                        mes_c = "C0100001巻上時間:" + '(' + so_time + '-' + sc_time + ')'
            if remote == '10':
                xbee.atcmd('d6', OFF)
                xbee.atcmd('d7', OFF)
                xbee.atcmd('d9', OFF)
                mes_c = 'C0100001リモート　OFF'
        if time_w <= now_time and t_w:
            xbee.atcmd('d2', OFF)
            xbee.atcmd('d3', OFF)
            t_w = False
            w_s = True
            k_time = s_time + 5
        if p_time <= now_time:
            p_time = now_time + 30
            temp_a = temp.read() * 0.030525 - 48.3
            if remote == '11' and select == '22':  # 自動
                if wall == '21':  # 温度
                    if temp_c <= temp_a - 3 and k_time <= s_time:
                        xbee.atcmd('d3', OFF)
                        xbee.atcmd('d2', ON)
                        if w_s:
                            print('temp_open')
                            time_w = now_time + 5
                            w_s = False
                            t_w = True
                    if temp_c >= temp_a + 3 and k_time <= s_time:  # ヒステリシス　5
                        xbee.atcmd('d2', OFF)
                        xbee.atcmd('d3', ON)
                        if w_s:
                            print('temp_close')
                            time_w = now_time + 5
                            w_s = False
                            t_w = True
                if wall == '22' and (d or everyday == '11'):  # 時間
                    if o_time <= s_time < c_time and p:
                        xbee.atcmd('d3', OFF)
                        xbee.atcmd('d2', ON)
                        # if p:
                        off_time = time.ticks_ms() + 120000
                        print('time_open')
                        p = False
                        o = True
                    if s_time >= c_time and not p:
                        xbee.atcmd('d2', OFF)
                        xbee.atcmd('d3', ON)
                        off_time = time.ticks_ms() + 120000
                        print('time_close')
                        p = True
                        o = True
                    if off_time <= time.ticks_ms() and o:
                        xbee.atcmd('d2', OFF)
                        xbee.atcmd('d3', OFF)
                        if everyday == '11':
                            d = True
                        if everyday == '10' and p:
                            d = False
                            xbee.atcmd('d9', OFF)
                            mes_c = "C0100001リモート ON"
                        o = False
            mes_a = "{0:.1f}".format(temp_a) + '℃' + "\x00"
            mes_a = 'A01' + "{:05.1f}".format(temp_a) + '温度:' + mes_a
            print(s_time)
            print(mes_c)
            print(mes_a)
            try:
                xbee.transmit(addr_coordinator, mes_c)
                xbee.transmit(addr_coordinator, mes_a)
            except OSError:
                xb_join()
        if now_time == 82800 and time_calibration:
            try:
                xbee.transmit(addr_coordinator, 'S')
                print('time calibration')
                time_calibration = False
            except OSError:
                xb_join()
                xbee.transmit(addr_coordinator, 'S')
                print('time calibration')
        if remote == '11' and not manual_sw.value():
            m = m + 1
            if m >= 100 and m_s:
                manual = not manual
                m_s = False
            if manual:
                xbee.atcmd('d4', ON)
            else:
                xbee.atcmd('d4', OFF)
        else:
            m = 0
            m_s = True
        if manual:
            if not open_sw.value() and close_sw.value():
                xbee.atcmd('d3', OFF)
                xbee.atcmd('d2', ON)
            else:
                xbee.atcmd('d2', OFF)
            if not close_sw.value() and open_sw.value():
                xbee.atcmd('d2', OFF)
                xbee.atcmd('d3', ON)
            else:
                xbee.atcmd('d3', OFF)


try:
    xb_join()
    main()
except Exception as e:
    print(e)
    time.sleep(2)
    machine.reset()
