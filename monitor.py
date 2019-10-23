from pymodbus.client.sync import ModbusTcpClient
import schedule
import time
import tweepy
import datetime
import logging

#getcontext().prec = 2

#TWITTER DEV SETTINGS
CONSUMER_KEY = ""
CONSUMER_SECRET = ""
ACCESS_KEY = ""
ACCESS_SECRET = ""

#Setup logging.
logging.config()

def get_data():
    for i in range(0,50):
        url = "192.168.1.1{num:02d}".format(num=i)
        client = ModbusTcpClient(url)
        if client.connect() == True:
            logging.info("Controller found in {}".format(url))
            #print(url)
            rr = client.read_holding_registers(0, 60, unit=1)
            client.close()
            return rr.registers

    return

def make_alert():
    data = get_data()
    charge_state = ['Start', 'Night Check', 'Disconnected', 'Night', 'Fault!', 'MPPT', 'Absorption', 'FloatCharge', 'Equalizing', 'Slave']

    alarms = ["RTS open", "RTS shorted", "RTS disconnected", "Heatsink temp sensor open",
          "Heatsink temp sensor shorted", "High temperature current limit", "Current limit",
          "Current offset", "Battery sense out of range", "Battery sense disconnected",
          "Uncalibrated", "RTS miswire", "High voltage disconnect", "Undefined",
          "system miswire", "MOSFET open", "P12 voltage off", "High input voltage current limit",
          "ADC input max", "Controller was reset", "Alarm 21", "Alarm 22", "Alarm 23", "Alarm 24"]

    faults = ["overcurrent", "FETs shorted", "software bug", "battery HVD", "array HVD",
              "settings switch changed", "custom settings edit", "RTS shorted", "RTS disconnected",
              "EEPROM retry limit", "Reserved", " Slave Control Timeout",
              "Fault 13", "Fault 14", "Fault 15", "Fault 16"]
    if data:
        logging.info("Data acquired")
        V_PU_hi = data[0]
        V_PU_lo = data[1]
        I_PU_hi = data[2]
        I_PU_lo = data[3]

        V_PU = float(V_PU_hi) + float(V_PU_lo)
        I_PU = float(I_PU_hi) + float(I_PU_lo)
        v_scale = V_PU * 2**(-15)
        i_scale = I_PU * 2**(-15)
        p_scale = V_PU * I_PU * 2**(-17)

        battery_voltage = round(float(data[24]) * v_scale,2)
        #print(battery_voltage)
        #charging_current = round(data[39] / current_scaling,2)
        charging_state = data[50]
        target_voltage = data[51]
        output_power = round(data[58] * p_scale,0)
        battery_temp = data[36]
        total_kwh = data[56]
        alarm = data[46]
        fault = data[44]

        text = "Battery {} V, temp {} C, power {} W, state {}. Total kWh {}.".format(
            battery_voltage, battery_temp, output_power, charge_state[charging_state], total_kwh)
        logging.info("Text to send {}".format(text))
        #print(text)
        return text


def publish():
    try:
        text = make_alert()
        #print(text)
        if text:
            auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
            auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
            api = tweepy.API(auth)
            api.update_status(text)
            logging.info("Text sent")
    except Exception as e:
        logging.info("Error ".format(e))
        #print (e)


schedule.every(30).minutes.do(publish)
print("Start time: {}".format(datetime.datetime.now()))

def test():
    text = "test msg {}".format(datetime.datetime.now())
        #print(text)
    if text:
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
        api = tweepy.API(auth)
        api.update_status(text)

##test()
publish()

while True:
    schedule.run_pending()
    time.sleep(1)
