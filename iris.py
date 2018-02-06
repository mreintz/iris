# -*- coding: utf-8 -*-
#import locale
#locale.setlocale(locale.LC_ALL, '')

import urllib2
import xml.etree.ElementTree as et
from datetime import datetime, date, timedelta
from calendar import HTMLCalendar
import pytz
import web
#from operator import itemgetter
import os
from shutil import copyfile
import socket
import re

urls = (
    '/iris/kalender', 'iriskalender',
    '/iris/varsel', 'irisvarsel',
    '/iris/settings', 'websettings',
    '/favicon.ico', 'icon'
)

class MyApplication(web.application):
    def run(self, port=8080, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))

settings_filename = 'iris.xml'
no_months = {
    'January': 'Januar',
    'February': 'Februar',
    'March': 'Mars',
    'April': 'April',
    'May': 'Mai',
    'June': 'Juni',
    'July': 'Juli',
    'August': 'August',
    'September': 'September',
    'October': 'Oktober',
    'November': 'November',
    'December': 'Desember'
}

no_days = {
    'Mon': 'Man',
    'Tue': 'Tir',
    'Wed': 'Ons',
    'Thu': 'Tor',
    'Fri': 'Fre',
    'Sat': u'Lør'.encode('latin-1'),
    'Sun': u'Søn'.encode('latin-1')
}

def isHN():
    host = socket.getfqdn()
    p = re.compile('.*hn.helsenord.no')
    result = p.match(host)
    if result:
        return True
    else:
        return False

def settings(**kwargs):
    tree = et.parse(settings_filename)
    root = tree.getroot()

    if kwargs:
        for p in kwargs.keys():
            try:
                e = root.find(p)
                e.text = kwargs[p]
            except AttributeError:
                root.append(et.Element(p))
                e = root.find(p)
                e.text = kwargs[p]

        tree.write(settings_filename)

    else:
        settings = {}
        for e in root:
            settings[e.tag] = e.text
        return settings
    return

def isAndroid():
    try:
        if os.uname()[4] == 'armv8l':
            return True
    except AttributeError:
        return False

if isAndroid():
    path = '/storage/emulated/0/qpython/scripts/'
    os.chdir(path)
    import androidhelper as android
    droid = android.Android()

def loadSettings():
    notify_tomorrow = settings()['notifyTomorrow']
    notify_today = settings()['notifyToday']
    number_of_months = settings()['numberOfMonths']
    last_notified_today = settings()['lastNotifiedToday']
    last_notified_tomorrow = settings()['lastNotifiedTomorrow']
    return notify_today, notify_tomorrow, int(number_of_months), last_notified_today, last_notified_tomorrow

class icon:
    def GET(self): raise web.seeother("/static/trash.ico")

class websettings:

    def GET(self):
        data = web.input()
        if data:
            for p in data.keys():
                if p == 'notifyToday':
                    klokkeslett = data[p]
                    if ( klokkeslett.isdigit() and len(klokkeslett) <= 2 and int(klokkeslett) <= 23 ):
                        settings(**{p: data[p]})
                        return 'Endrer klokkeslett for varsel i dag til {0}'.format(klokkeslett)
                    else:
                        return 'Ikke gyldig'
                elif p == 'notifyTomorrow':
                    klokkeslett = data[p]
                    if ( klokkeslett.isdigit() and len(klokkeslett) <= 2 and int(klokkeslett) <= 23 ):
                        settings(**{p: data[p]})
                        return 'Endrer klokkeslett for varsel i morgen til {0}'.format(klokkeslett)
                    else:
                        return 'Ikke gyldig'
                elif p == 'numberOfMonths':
                    number = data[p]
                    if ( number.isdigit() and int(number) <= 6 ):
                        settings(**{p: data[p]})
                        return u'Endrer antall måneder til {0}'.format(number).encode('latin-1')
                    else:
                        return 'Ikke gyldig'
                else:
                    set = settings()
                    output = '<html><body><table><tr><th>Parameter</th><th>Verdi</th></tr>'
                    for s in set.keys():
                        output += '<tr><td class="setting">{0}</td><td>{1}</td></tr>'.format(s, set[s])
                    output += '</table></body></html>'
                    return output
        else:
            set = settings()
            output = '<html><head><link rel="stylesheet" type="text/css" href="/static/kalenderstil.css"></head><body><table><tr><th>Parameter</th><th>Verdi</th></tr>'
            for s in set.keys():
                output += '<tr><td class="setting">{0}</td><td>{1}</td></tr>'.format(s, set[s])
            output += '</table></body></html>'
            return output

def loadData():

    def formatTimeString(date):
        time = pytz.timezone('Europe/Oslo').localize(date)
        timestring = datetime.strftime(datetime.date(date), '%Y-%m-%dT%H:%M:%S')
        timestring = timestring+time.strftime('%z').replace('00', ':00')
        return timestring

    today = datetime.now()
    fromdate = datetime(today.year, today.month, 1)
    todate = datetime(today.year + (today.month+7) / 12, (today.month+7) % 12 + 1, 1)

    data = """<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>
        <GetCollectionCalendar xmlns="http://tempuri.org/">
        <username>nois</username>
        <password>nois</password>
        <collectionpointid>15847</collectionpointid>
        <collectionpointidSpecified>true</collectionpointidSpecified>
        <fromDate>{0}</fromDate>
        <fromDateSpecified>true</fromDateSpecified>
        <toDate>{1}</toDate>
        <toDateSpecified>true</toDateSpecified>
        </GetCollectionCalendar>
        </soap:Body></soap:Envelope>""".format(formatTimeString(fromdate), formatTimeString(todate)) # 2017-04-02T00:00:00+02:00, 2017-12-31T00:00:00+02:00

    url = 'http://77.110.220.150:82/SyncService/basic'

    request_headers = {
    "User-Agent": "Mono Web Services Client Protocol 4.0.50524.0",
    "SOAPAction": "http://tempuri.org/ISyncEngine/GetCollectionCalendar",
    "Content-Type": "text/xml; charset=utf-8",
    "Content-Length": "{0}".format(len(data)),
    "Expect": "100-continue",
    "Connection": "keep-alive",
    "Host": "77.110.220.150:82"
    }

    method = 'POST'

    if isHN():
        proxy_handler = urllib2.ProxyHandler({'http': 'www-proxy.helsenord.no:8080'})
        opener = urllib2.build_opener(proxy_handler)
    else:
        handler = urllib2.HTTPHandler()
        opener = urllib2.build_opener(handler)

    lastDownloadedDate = datetime.strptime(settings()['lastDownloaded'], '%Y-%m-%d')
    diff = today - lastDownloadedDate

    if diff.days > 7:
        try:
            print "Laster ned data fra webtjeneste."
            if isAndroid():
                droid.makeToast("Laster ned data fra webtjeneste...")
            request = urllib2.Request(url, data=data)
            for r in request_headers:
                request.add_header(r, request_headers[r])
            request.get_method = lambda: method
            tree = et.parse(opener.open(request))

            print "Lagrer dato for siste nedlasting."
            settings(lastDownloaded=datetime.strftime(today, '%Y-%m-%d'))

            print "Lagrer siste nedlasting."
            try:
                copyfile('iris_download.xml', 'iris_download.bak')
            except IOError:
                print "Ingen gammel lagret fil."
            tree.write('iris_download.xml')
        except urllib2.HTTPError:
            print "Ikke tilgang til nett. Parser lokale data."
            tree = et.parse('iris_download.xml')
        except IOError as e:
            print "Brutt nettverksforbindelse. Parser lokale data."
            tree = et.parse('iris_download.xml')
    else:
        print "Parser lokale data."
        tree = et.parse('iris_download.xml')

    root = tree.getroot()
    nsa = 'http://schemas.datacontract.org/2004/07/ISY.ProAktiv.Sync'
    items = root.findall('.//{%s}PACollectionCalendarItem' %(nsa))

    avfallskalender = {}
    for i in items:
        date = i.find('.//{%s}CollectionDate' %(nsa)).text
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
        formatdate = datetime.strftime(date, '%Y-%m-%d')

        kode = i.find('.//{%s}RouteName' %(nsa)).text

        try:
            if avfallskalender[formatdate]:
                kode = avfallskalender[formatdate][0]+','+kode
                a_type = i.find('.//{%s}ProductDescription' %(nsa)).text
                avfallstype = avfallskalender[formatdate][1]
                avfallstype.append(a_type)
        except KeyError:
            avfallstype = []
            a_type = i.find('.//{%s}ProductDescription' %(nsa)).text
            avfallstype.append(a_type)

        avfallskalender[formatdate] = [kode, avfallstype, date]

    return avfallskalender

def color(code):
    return{
        'P': '#0099ff',
        'M': '#996600',
        'R': 'gray'
    }.get(code, '#33cc33')

def formatAvfallskalender(avfallskalender, date):
    month = date.month
    year = date.year
    cal = HTMLCalendar()
    mymonth = cal.formatmonth(year, month, withyear=True)
    for m in no_months.keys():
        mymonth = mymonth.replace(m, no_months[m])

    for d in no_days.keys():
        mymonth = mymonth.replace(d, no_days[d])

    if date.month == datetime.now().month:
        mymonth = mymonth.replace('>'+str(datetime.now().day)+'<', '  style="border-width:6px;border-color:red;">'+str(datetime.now().day)+'<')

    for a in avfallskalender:
        if avfallskalender[a][2].month == month:
            mymonth = mymonth.replace('>'+str(avfallskalender[a][2].day)+'<', ' bgcolor="{0}">'+avfallskalender[a][0]+'<').format(color(avfallskalender[a][0]))

    return mymonth

class iriskalender():
    def GET(self):
        output = '<html><head><link rel="stylesheet" type="text/css" href="/static/kalenderstil.css"><meta name="mobile-web-app-capable" content="yes"></head>'
        output += '<body><h1>{0}</h1>'.format(u'Tømmekalender'.encode('latin-1')) #<p><table width="100%">

        avfallskalender = loadData()
        today = datetime.now()

        todaystring = datetime.strftime(today, '%Y-%m-%d')
        tomorrowstring = datetime.strftime(today+timedelta(days=1), '%Y-%m-%d')

        bottomstring = ''

        try:
            if avfallskalender[tomorrowstring]:
                bottomstring += 'I morgen er det {0}. '.format(', '.join(avfallskalender[tomorrowstring][1]))
        except KeyError:
            pass

        try:
            if avfallskalender[todaystring]:
                bottomstring += 'I dag er det {0}. '.format(', '.join(avfallskalender[todaystring][1]))
        except KeyError:
            pass

        notify_today, notify_tomorrow, number_of_months, last_notified_today, last_notified_tomorrow = loadSettings()

        for thismonth in range(number_of_months):
            if today.month + thismonth == 12:
                date = datetime(today.year, 12, 1)
            else:
                date = datetime(today.year + (today.month + thismonth)/12, (today.month + thismonth)%12, 1)
            outmonth = formatAvfallskalender(avfallskalender, date)
            output += '<p>'+outmonth+'<br>'

        if bottomstring == '':
            output += u'<p><a class="notify" href="http://127.0.0.1:8099/iris/settings">Du blir varslet klokka {0} samme dag og klokka {1} dagen før.</a>'.format(str(notify_today), str(notify_tomorrow)).encode('latin-1')
        else:
            output += u'<p><a class="notify" href="http://127.0.0.1:8099/iris/settings">{0}</a>'.format(bottomstring).encode('latin-1')
        output += '</body></html>'
        return output

class irisvarsel():
    def GET(self):
        avfallskalender = loadData()
        notify_today, notify_tomorrow, number_of_months, last_notified_today, last_notified_tomorrow = loadSettings()

        for a in avfallskalender.keys():
            typer = avfallskalender[a][1]
            koder = avfallskalender[a][0]
            today = datetime.now()
            tmr = date.today() + timedelta(days=1)
            tomorrow = datetime(tmr.year, tmr.month, tmr.day)

            if a == datetime.strftime(today, '%Y-%m-%d') and today.hour == int(notify_today) and datetime.strftime(today, '%Y-%m-%d') != last_notified_today:
                out = ''
                i = 1
                for t in typer:
                    if i == 1:
                        out = t
                    else:
                        out += ', '+t
                    i = i + 1

                if isAndroid():
                    #droid.notify(u'Søppeltømming!', u'Søppeltømming! I dag er det {0}.'.format(out) )
                    with open('/storage/emulated/0/qpython/scripts/static/message.txt', 'w') as f:
                        f.write('Søppeltømming!::I dag er det {0}.'.format(out))
                        f.close()

                settings(lastNotifiedToday=datetime.strftime(today, '%Y-%m-%d'))
                return '<p>Søppeltømming! I dag er det {0}.<p>.'.format(out)

            if a == datetime.strftime(tomorrow, '%Y-%m-%d') and today.hour == int(notify_tomorrow) and datetime.strftime(today, '%Y-%m-%d') != last_notified_tomorrow:
                out = ''
                i = 1
                for t in typer:
                    if i == 1:
                        out = t
                    else:
                        out += ', '+t
                    i = i + 1

                if isAndroid():
                    #droid.notify(u'Søppeltømming!', u'Søppeltømming! I morgen er det {0}.'.format(out) )
                    with open('/storage/emulated/0/qpython/scripts/static/message.txt', 'w') as f:
                        f.write('Søppeltømming!::I morgen er det {0}.'.format(out))
                        f.close()

                settings(lastNotifiedTomorrow=datetime.strftime(today, '%Y-%m-%d'))
                return '<p>Søppeltømming! I morgen er det {0}.<p>.'.format(out)

        return '<p>Ingen varsler.<p>.'


if __name__ == '__main__':
    app = MyApplication(urls, globals())
    app.run(port=8099)
