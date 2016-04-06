import time
import sys
import urllib
import requests
import xml.etree.ElementTree as et
from BeautifulSoup import *

'''
Examples code_sec:
FUT  --> Si-3.16
CALL --> Si-3.16M210116CA 51750
PUT  --> Si-3.16M210116PA 62250
'''

FUT_URL   = 'http://moex.com/ru/derivatives/contractresults.aspx?code='
STOCK_URL = 'http://www.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/'


def getHtml(url):
    return urllib.urlopen(url).read().decode('utf-8')


def getXml(url):
    try:
        return urllib.urlopen(url).read()
    except:
            print "--> Error in moex_eod.getXml():", sys.exc_info()[0]
            time.sleep(1)
            return getXml(url)


def getStockPrice(xml):
    tree = et.fromstring(xml)
    return tree.find('.//row').get('LEGALCLOSEPRICE')


def printFutPrice(html, date):
    bsoup = BeautifulSoup(html)
    tags  = bsoup('td')

    for tag in tags:
        if tag.text == date:            
            ptag    = tag.findParent()            
            settlep = ptag.contents[2].text
            openp   = ptag.contents[3].text
            highp   = ptag.contents[4].text
            lowp    = ptag.contents[5].text
            closep  = ptag.contents[6].text

            print 'date:   ' , date
            print 'settle: ' , settlep
            print 'open:   ' , openp
            print 'high:   ' , highp
            print 'low:    ' , lowp
            print 'close:  ' , closep
            print 
            break
    else:
        print 'date: {0} --> NOT FOUND'.format(date)
        print 


def main():
##    sec_code = 'Si-3.15'
##    dates = ['30.01.2011','15.02.2015','17.02.2015']
##    url = FUT_URL + sec_code
##    html = getHtml(url)
##    if len(html) > 0:
##        for date in dates:
##            printFutPrice(html, date)

    sec_id = 'SBERP'
    date = '2015-12-15'
    url = STOCK_URL + '{0}.xml?from={1}&till={1}&lang=RU'.format(sec_id, date)
    xml = getXml(url)    
    if len(xml) > 0:
        print getStockPrice(xml)


if __name__ == '__main__':
    main()


