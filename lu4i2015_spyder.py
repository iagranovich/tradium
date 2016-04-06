'''
' Making trader equity from list of trades.
'''

import urllib
import requests
import re
import time
import sys
import json
from BeautifulSoup import BeautifulSoup
from datetime import datetime, date, timedelta
from decimal import Decimal as dec

import moex_eod as eod


URL = 'http://investor.moex.com/ru/statistics/2015/default.aspx'
FTP_URL = 'ftp://ftp.moex.com/pub/info/stats_contest/2015/all/'
POS_URL = 'http://investor.moex.com/ru/statistics/2015/portfolio.aspx/GetPortfolioData'
MIN_QTY_TRADES = 59 #set to 59
MAX_QTY_TRADES = 2001 #set to 2001
MAX_DATE = date(2015, 10, 1) #date(2015, 10, 1)


def datefstr(date_str):
    '''
    ' input: DD.MM.YYYY
    ' output: YYYY-MM-DD
    '''    
    dt = [int(d) for d in date_str.split('.')]
    return date(dt[2], dt[1], dt[0])


def get_id(raw_id):
    '''
    ' Get trader_id from diagram link on moex site.
    ' Another solution is to go to ftp:
    ' ftp://ftp.moex.com/pub/info/stats_contest/2015/trader.csv
    '''
    return re.search('user=([0-9]+)', raw_id).group(1)


def download(url, trader_id, path):
    urllib.urlretrieve('{0}1_{1}.zip'.format(url, trader_id),
                       '{0}1_{1}.zip'.format(path, trader_id))


def get_html(url):
    return urllib.urlopen(url).read().decode('utf-8')


def get_html2(params, url):
    '''
    Get contest stats page.
    -------------------------
    Params:
    @page - stats page number
    @contest - nomination number, 1 - 'fondovii rinok' 
    '''
    
    all_params = {'act':'', 'sby':'8', 'nick':'', 'data-contype-id-1':'',
                  'data-contype-id-2':'', 'data-contype-id-3':'', 'pge':params['page'],
                  'type':'0', 'date':'20151215', 'gr':params['contest'], 'snick':''}
    html = requests.post(url, data = all_params)
    return html.text

    	
def get_info(html):
    '''
    ' Information for each trader from one page
    '''

    bs = BeautifulSoup(html)
    table = bs.find('table', {'class':'tablels'})
    info = []

    '''
    ' contents[3] - Nickname
    ' contents[7] - registration date
    ' contents[9] - starting capital
    ' contents[11] - amount of orders
    ' contents[13] - amount of trades
    ' contents[17] - return
    ' contents[19] - trader id
    '''
    
    for tr in table.tr.findNextSiblings():        
        if len(tr.contents) > 20:
            minimum = min(int(tr.contents[11].text.replace('-','0')),
                          int(tr.contents[13].text.replace('-','0')))        
            if datefstr(tr.contents[7].text) < MAX_DATE: 
                if minimum > MIN_QTY_TRADES:
                    if minimum < MAX_QTY_TRADES:                        
                        info.append(dict([('nick', tr.contents[3].text.replace(u'\u2022', u'')),
                                          ('date', tr.contents[7].text),
                                          ('init_cap', tr.contents[9].text.replace(u'\xa0', u'').replace(',', '.')), #TODO: make method for deleting irregular symbols
                                          ('trades', minimum),
                                          ('return', tr.contents[17].text),
                                          ('id', get_id(tr.contents[19].a.attrs[3][1]))]))
    return info


def getPositions(params, url):    
    response = requests.post(url, json = params).json()
    return json.loads(response['d'])


def getRegistrationDate(trader_id, info):
    #registr_date = None
        for entry in info:
            if trader_id == entry['id']:
                return datefstr(entry['date'])
                
        else:
            print '--> Trader_Id NOT FOUND'
            return None


def parse_helper():
    html = get_html2(1, 1, URL)
    bsoup = BeautifulSoup(html)
    table = bsoup.find('table', {'class' :'tablels'})
    for att in table.contents[3].contents[19].a.attrs:
        print att


def main():     
    for i in range(1,2):
        html = get_html2({'page':i, 'contest':1}, URL)
        if len(html) > 0:            
            for info in get_info(html):               
                try:
                    print 'Nickname: {0}; return = {1}'.format(info['nick'], info['id'])
                    download(FTP_URL, info['id'], 'data/')                    
                except UnicodeEncodeError:##?
                    print '--> UnicodeEncodeError' 
        time.sleep(1)


            
'''    
TODO:
1) add @property, @.setter
2) add exceptions where need
3) add evaluation by the end of each day
'''
class Stock:
    def __init__(self, sname):
        self.sname = sname
        #self.init_pos = []
        self.trades = []
        self.vmargin = []

    def addTrade(self, trade):
        keys = ['date', 'name', 'qty', 'price']
        self.trades.append(
            dict(zip(keys, [t.strip() for t in trade.split(';')])))

    def vMargin(self):
        '''
        ' !Calculate only after all trades added!
        '''
        
        if len(self.trades) == 0:
            print '--> Trades list IS EMPTY'
            return
        if len(self.trades) == 1:
            '''
            TODO: rewrite to method which estimates open positions
                  every day by the end of the contest.
            -------------------
            If there is only one trade then evaluate by the end of contest.
            '''
            
            url = eod.STOCK_URL + '{0}.xml?from={1}&till={1}&lang=RU'.\
                                   format(self.sname, '2015-12-15')
            xml = eod.getXml(url)    
            if len(xml) > 0:
                try:
                    price = eod.getStockPrice(xml)
                except:
                    print '--> Stock {0} - NOT FOUND'.format(self.sname)
                    price = self.trades[0]['price']
                qty = self.trades[0]['qty']
                format_ = ['2015-12-15 18:45:00.000', self.sname, qty, price]
                self.addTrade('{0};{1};{2};{3}'.format(*format_))
            else:
                print '--> XML for getStockPrice() from moex_eod.py NOT FOUND'
                return

        #if number of trades more than 1        
        position = 0
        for i in range(0, len(self.trades) - 1):
            dt  = self.trades[i + 1]['date']
            pr1 = self.trades[i]['price']
            pr2 = self.trades[i + 1]['price']
            qty = self.trades[i]['qty']
            position += int(qty)
            vm  = position*(dec(pr2) - dec(pr1))
            self.vmargin += [{'date':dt, 'vmargin':vm}]

        return self.vmargin


class Portfolio(dict):
    pass


'''TODO:
1) make class Portfolio(dict) as Collection
2) add @property, @.setter
'''
class Trader:
    def __init__(self, tid, reg_date, path):
        self.portf = []
        self.tname = ''
        self.tid = tid
        self.reg_date = reg_date
        self.path = path        
        self.setInitPos(self.reg_date)
        self.openFile(self.path)


    def setInitPos(self, reg_date):
        '''
        ' Initial position like a first trade
        '-------------------------------
        ' reg_date - registarition date
        '''
        
        while True:
            params = {'traderId':self.tid,'date':str(reg_date),'tableId':6}
            poses = getPositions(params, POS_URL)            
            if len(poses) < 1:
                reg_date += timedelta(days = 1)                
                continue
            for pos in poses:               
                p = pos['pos'].split(' ') # pos['pos'] = '-99 (-)'
                #checking existence starting positions:
                if int(p[0]) != 0 and int(p[0]) != int(p[1].strip('()').replace('-','0')):
                    sname = pos['seccode']
                    #stock ticker has max 5 charecters:
                    if len(sname) < 6:
                        continue
                    self.addNewStock(sname)
                    stock = self.getStock(sname)
                    format_ = [str(reg_date), sname, p[0], pos['cena']]
                    stock.addTrade('{0};{1};{2};{3}'.format(*format_))
            break
        

    def openFile(self, path):
        fh = None        
        try:
            fh = open(path, 'r')
            for line in fh.readlines():
                sname = line.split(';')[1].strip()
                if sname not in self.getAllStockNames():
                    self.addNewStock(sname)
                self.getStock(sname).addTrade(line)   
        except IOError:
            print '--> File NOT FOUND'
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise
        finally:
            if fh is not None:
                fh.close()
                

    '''TODO: add stock name??'''
    def vmPortfolio(self):
        '''Total portfolio margin'''
        vm = []
        for stock in self.portf:            
            vm += stock.vMargin()
        return sorted(vm, key = lambda d: d['date'])           
                

    def getAllStockNames(self):
        return [stock.sname for stock in self.portf]
    

    def getStock(self, sname):
        for stock in self.portf:                    
            if sname == stock.sname:
                return stock
            

    def addNewStock(self, sname):
        self.portf += [Stock(sname)]
                


if __name__ == '__main__':
##     main()
    
    #create info:
    info = []
    for i in range(1,114):#113 pages
        html = get_html2({'page':i, 'contest':1}, URL)
        if len(html) > 0:            
            info += get_info(html)

    #dowload files from MOEX ftp:
    '''for trader in info:
        download(FTP_URL, trader['id'], 'data/') '''

    raw_input('--> Please, unzip files and press Enter...')

    #create equity 'trader_id.csv' file for each trader from info:
    for row in info:
        rdate = datefstr(row['date'])
        tid = row['id']
        path = 'data/1_{0}.csv'.format(tid)
        trader = Trader(tid, rdate, path)

        #make equity:
        vmargin = trader.vmPortfolio()
        rdatetime = str(datefstr(row['date'])) + ' 10:00:00.000'
        init_cap = dec(row['init_cap'])
        equity = [{'date':rdatetime, 'val':init_cap}]
        i = 0
        for i,vm in enumerate(vmargin):
            eq = equity[i]['val'] + vm['vmargin'] 
            equity += [{'date':vm['date'], 'val':eq}]

        #compare returns with site:
        from_moex_return = dec(row['return'].replace(',','.'))
        calculated_return = (equity[i]['val'] / equity[0]['val'] - 1) * 100
        tol = from_moex_return * dec(0.15) #tolerance 15%
        if calculated_return > from_moex_return + tol or calculated_return < from_moex_return - tol:
            print 'id: {0}, moex_ret = {1}, calc_ret = {2}'.format(row['id'], from_moex_return, calculated_return)
            continue

        #write equity to file
        with open('data/{0}.csv'.format(tid), 'w') as f:
            for eq in equity:
                f.write('{0};{1}\n'.format(eq['date'], eq['val']))

                
