from flask import Flask, render_template, request, make_response, session
import pycountry
import requests

app = Flask(__name__)
app.secret_key = 'cyklar'
# en hemligt key behövs för att session ska kunna köras.


def get_country_city_data():
    """
    Hämtar data från API:et för att extrahera information om städer och länder.

    returnerar sorterade landsnamn och städer.
    """

    api_url = 'http://api.citybik.es/v2/networks'
    response = requests.get(api_url)

    country_names = set()  # En uppsättning för  landsnamn
    cities = set()  # En uppsättning för städer

    if response.status_code == 200:
        data = response.json()
        networks = data.get('networks', [])  # Hämtar listan med nätverk från API:et

        for network in networks:
            location = network.get('location', {})  # Extraherar information om platsen från nätverket
            country_code = location.get('country', '')  # Hämtar landskoden
            country = pycountry.countries.get(alpha_2=country_code)  # Konverterar landskoden till landsnamn
            country_name = country.name if country else 'Okänt land'  # Säkerställer giltigt landsnamn
            country_names.add(country_name)  # Lägger till landsnamnet i uppsättningen av unika landsnamn
            cities.add(location.get('city', ''))  # Lägger till staden i uppsättningen av unika städer från platsdict

        return sorted(country_names), sorted(list(cities))

    return [], []


def get_stations_by_country(country_code):
    """
    Hämtar cykelstationer för ett specifikt land.

    country_code (str): Landskod för det land där stationerna ska hämtas.

    List: En lista med cykelstationer i det valda landet.
    """

    api_url = 'http://api.citybik.es/v2/networks'
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        networks = data.get('networks', [])
        stations = []

        for network in networks:
            location = network.get('location', {})  # Extraherar information om platsen från dict
            if location.get('country') == country_code:
                stations.append(network)  # Om landskoden matchar, läggs stationen till i listan

        return stations


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Hämta det valda landet från formuläret och lagra det i en variabel
        selected_country = request.form['country']

        # Lagra det valda landet i Flask-sessionen
        session['selected_country'] = selected_country
    else:
        # försök att hämta 'selected_country' från sessionen, eller använd 'all' som standard om det inte finns
        selected_country = session.get('selected_country', 'all')

    # Anropa funktionen get_country_city_data för att hämta landsnamn och städer
    country_names, cities = get_country_city_data()

    # Skapa en tom lista för att lagra stationsdata
    stations = []

    if request.method == 'POST':
        # Hämta det valda landet från formuläret
        country_name = request.form['country']

        # Kontrollera om 'Alla länder' valdes i rullgardinsmenyn
        if country_name == 'Alla länder':
            # Om 'Alla länder' är valt, hämta stationer för alla länder
            stations = get_stations_by_country('')
        else:
            # Om ett specifikt land är valt, hitta dess alfa-2 landskod
            country_code = pycountry.countries.lookup(country_name).alpha_2

            # Hämta stationer för det valda landet
            stations = get_stations_by_country(country_code)

    return render_template('index.html', stations=stations, countries=country_names, cities=cities,
                           selected_country=selected_country)


if __name__ == '__main__':
    app.run(debug=True)
