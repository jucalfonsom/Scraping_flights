# Web Scrapping de la aerolinea Viva Air de Colombia
# Autor: Juan Camilo Alfonso Mesquida
# Fecha: 22/10/2020


import pandas as pd
import os
from datetime import date
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


def _main(url):
    print('-' * 50)  
    print('Inicio ejecución')  
    driver = _open_sesion(url)
    flights = get_flights(driver)
    if len(flights) > 0:
        flights_df = get_flights_information(driver, flights)
    
    _save_data(flights_df)

    _close_sesion(driver)


def _open_sesion(url):
    delay = 10

    try:
        print(f'Abriendo explorador Chrome')
        options = webdriver.ChromeOptions()
        options.add_argument('--incognito')
        driver = webdriver.Chrome(executable_path='dchrome/chromedriver.exe', options=options)

        driver.get(url)
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//div[@class = "flight"]')))
        print('La página terminó de cargar')
        
        return driver

    except TimeoutException:
        print('La página tardó demasiado en cargar, no se pudieron obtener vuelos')

        return None


def get_flights(driver):

    try:
        flights = driver.find_elements_by_xpath('//div[@class = "flight"]')
        print(f'Se obtuvieron {len(flights)} vuelos')

        return flights

    except TimeoutException:
        print('La página tardó demasiado en cargar, no se pudieron obtener vuelos')

        return None


def get_flights_information(driver, flights):
    flights_df = pd.DataFrame(columns=['Hora Salida', 'Hora llegada',
                                        'Duración', 'Escalas',
                                        'Ciudad salida escala', 'Hora salida escala',
                                        'Ciudad llegada escala', 'Hora llegada escala',
                                        'Duración parada', 'Ciudad salida escala 2',
                                        'Hora salida escala 2', 'Ciudad llegada escala 2',
                                        'Hora llegada escala 2', 'Tarifa A la carta',
                                        'Tarifa Combo+', 'Tarifa Combo++', 'Moneda'])

    try:

        for  flight in flights:
            # Get flight information
            print(f'Extrayendo información del vuelo')
            flight_hours = flight.find_elements_by_xpath('.//div[@class = "time"]')
            departure_time = flight_hours[0].text
            arrival_time = flight_hours[1].text
            flight_duration = flight.find_element_by_xpath('.//div[@class = "duration"]').text.split('-')[0]
            stop_info = flight.find_element_by_xpath('.//div[@class = "duration"]').text.split('-')[1]

            # Get stop information
            try:
                stop_button = flight.find_element_by_xpath('.//span[@class = "view-stops"]')
                stop_button.click()
                stop_segments = flight.find_elements_by_xpath('//div[@class="segment-step"]')
                print(f'Se han encontrado: {len(stop_segments)-1} escalas')
                if len(stop_segments) > 0:
                    print('Extrayendo información de la escala')
                    stop_button.click()
                    stop_city_departure_1, stop_departure_time_1, stop_city_arrival_1, stop_arrival_time_1, stop_duration = get_stop_information(stop_segments[0])
                    stop_city_departure_2, stop_departure_time_2, stop_city_arrival_2, stop_arrival_time_2, stop_duration = get_stop_information(stop_segments[1])
                    stop_button.click()
            except Exception as e:
                stop_city_departure_1 = None
                stop_departure_time_1 = None
                stop_city_arrival_1 = None
                stop_arrival_time_1 = None
                stop_duration = None
                stop_city_departure_2 = None
                stop_departure_time_2 = None
                stop_city_arrival_2 = None
                stop_arrival_time_2 = None
                stop_duration = None
                print('El vuelo no tiene escalas')

            #Get flight cost
            rate_currency = 0
            economic_rate = 0
            average_rate = 0
            plus_rate = 0
            # rate_currency, economic_rate, average_rate, plus_rate = get_flight_cost(flight)


            flights_df = flights_df.append({'Hora Salida': departure_time,
                                            'Hora llegada': arrival_time,
                                            'Duración' : flight_duration,
                                            'Escalas' : stop_info,
                                            'Ciudad salida escala' : stop_city_departure_1,
                                            'Hora salida escala' : stop_departure_time_1,
                                            'Ciudad llegada escala' : stop_city_arrival_1,
                                            'Hora llegada escala' : stop_arrival_time_1,
                                            'Duración parada' : stop_duration,
                                            'Ciudad salida escala 2' : stop_city_departure_2,
                                            'Hora salida escala 2' : stop_departure_time_2,
                                            'Ciudad llegada escala 2' : stop_city_arrival_2,
                                            'Hora llegada escala 2' : stop_arrival_time_2,
                                            'Tarifa A la carta' : economic_rate,
                                            'Tarifa Combo+' : average_rate,
                                            'Tarifa Combo++' : plus_rate,
                                            'Moneda' : rate_currency
                                            }, ignore_index=True)  

        return flights_df

    except Exception as e:
        print(f'Error al tratar de extraer la información del vuelo de tipo: {e}')

        return None


def get_stop_information(stop_segment):
    stop_departure = stop_segment.find_elements_by_xpath('.//div[@class="segment-step-airport"]')[0].text
    stop_city_departure = stop_departure.split('\n')[0]
    stop_departure_time = stop_departure.split('\n')[1]
        
    stop_arrival = stop_segment.find_elements_by_xpath('.//div[@class="segment-step-airport"]')[1].text
    stop_city_arrival = stop_arrival.split('\n')[0]
    stop_arrival_time = stop_arrival.split('\n')[1]
        
    stop_duration = stop_segment.find_element_by_xpath('//div[@class="stop-indicator"]').text
    stop_duration = stop_duration.split()[1]

    return stop_city_departure, stop_departure_time, stop_city_arrival, stop_arrival_time, stop_duration


def get_flight_cost(flight):
    try:
        flight.find_element_by_xpath('.//div[@class = "segment-lowest-price isSelected"]').click()

        rates = flight.find_elements_by_xpath('//div[@class="fare-information-container"]//div[@class="price bold"]')
        rate_currency = rates[0].text.split()[0]
        economic_rate = rates[0].text.split()[1]
        average_rate = rates[1].text.split()[1]
        plus_rate = rates[0].text.split()[1]

        flight.find_element_by_xpath('.//div[@class = "segment-lowest-price isSelected"]').click()

        return rate_currency, economic_rate, average_rate, plus_rate
    
    except Exception as e:
        print(f'Error al tratar de extraer la información de las tarifas del vuelo de tipo: {e}')
    

def _save_data(flights_df):
    
    try:
        export_path = f'Vuelos_VivaAir_{date.today()}.csv'
        print('Descargando información en la ruta: {0}\\{1}'.format(os.getcwd(), export_path))
        flights_df.to_csv(r'{0}'.format(export_path), encoding='utf-8-sig', sep = ';', ind)

    except  Exception as e:
        print(f'Error al tratar de guardar la información: {e}')


def _close_sesion(driver):
    driver.close()


if __name__ == "__main__":
    url = 'https://www.vivaair.com/co/es/vuelo?DepartureCity=BOG&ArrivalCity=ADZ&DepartureDate=2021-04-01&ReturnDate=2021-04-11&Adults=2&Currency=COP'
    _main(url)