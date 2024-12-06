#
# Open Live Departure Boards Web Service (OpenLDBWS) API Demonstrator
# Copyright (C)2018-2024 OpenTrainTimes Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public Licensec
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from zeep import Client, Settings, xsd
from zeep.plugins import HistoryPlugin

from dotenv import load_dotenv
import time
import datetime
import os
import click

def in_between(now, start, end):
    if start <= end:
        return start <= now < end
    else:
        return start <= now or now < end

def displayStationBoard(res, destCRS):
    print(f"Trains from {res.locationName} to {res.filterLocationName}" )
    print("===============================================================================")

    if not res.trainServices:
        print("No trains in the next 120 minutes at this time")
        print("===============================================================================")
        return
    services = res.trainServices.service

    for t in services:
        line = f"{t.std} to {t.destination.location[0].locationName} - {t.etd}"
        if t.platform:
            line += f" - pl.{t.platform}"
        if t.subsequentCallingPoints:
            callingPoints = t.subsequentCallingPoints.callingPointList[0].callingPoint
            for callP in callingPoints:
                if callP.crs == destCRS:
                    line += f" - dest {callP.st} ETA {callP.et}"
        if t.cancelReason:
            line += f"\n{t.cancelReason}"
        print(line)
    print("===============================================================================")

class Dashboard:
    def __init__(self,START_ST,END_ST):
        self.START_ST = START_ST
        self.END_ST = END_ST

        self.setup_api()

    def setup_api(self):
        load_dotenv()

        LDB_TOKEN = os.getenv("RAIL_TOKEN")
        WSDL = 'http://lite.realtime.nationalrail.co.uk/OpenLDBWS/wsdl.aspx?ver=2021-11-01'

        if LDB_TOKEN == '':
            raise Exception("Please configure your OpenLDBWS token in getDepartureBoardExample!")

        settings = Settings(strict=False)

        history = HistoryPlugin()

        self.client = Client(wsdl=WSDL, settings=settings, plugins=[history])

        header = xsd.Element(
            '{http://thalesgroup.com/RTTI/2013-11-28/Token/types}AccessToken',
            xsd.ComplexType([
                xsd.Element(
                    '{http://thalesgroup.com/RTTI/2013-11-28/Token/types}TokenValue',
                    xsd.String()),
            ])
        )
        self.header_value = header(TokenValue=LDB_TOKEN)

    def run(self):
        while True:
            os.system('cls||clear')

            res = self.client.service.GetDepBoardWithDetails(numRows=10, crs=self.START_ST, filterCrs=self.END_ST, timeOffset=0, timeWindow=119, _soapheaders=[self.header_value])
            displayStationBoard(res,self.END_ST)

            res = self.client.service.GetDepBoardWithDetails(numRows=10, crs=self.END_ST, filterCrs=self.START_ST, timeOffset=0, timeWindow=119,   _soapheaders=[self.header_value])
            displayStationBoard(res,self.START_ST)
            line = f"Last updated: {res.generatedAt}"
            if in_between(datetime.datetime.now().time(),datetime.time(7),datetime.time(9)):
                line += " - Next update in 30s"
                sleepTime = 30
            elif in_between(datetime.datetime.now().time(),datetime.time(16),datetime.time(19)):
                line += " - Next update in 30s"
                sleepTime = 30
            else:
                line += " - Next update in 5m"
                sleepTime = 60*5
            print(line)
            time.sleep(sleepTime)

@click.command()
@click.option('--start-st',default='SWT',help="Starting station code e.g SWT MAN")
@click.option('--end-st',default='MAN', help="Destination statino code e.g LMS MAN")
def main(start_st,end_st):
    """
    Show a departure board

    Provide OpenLDBWS API token as env var: RAIL_TOKEN

    
    """
    dash = Dashboard(start_st,end_st)
    dash.run()

if __name__ == "__main__":
    main()
   
