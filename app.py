import serial
import threading
import time
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Configurações da balança
mocked_data = {
    "id_pedido": 1,
    "id_balanca": 1,
    "taxa_maxima": 5.0,
    "taxa_minima": 3.0,
    "peso_padrao": 2.0,
    "peso_bandeja": 0.8,
}
peso_atual = 0
estado = "desconhecido"
running = True  # Controle para a thread
vlr_final = 0

# Função para extrair peso
def extract_weight(data):
    try:
        if len(data) >= 13 and (data.startswith("<q") or data.startswith("<p")):
            weight_str = data[3:9]
            weight_in_grams = int(weight_str)
            tare_str = data[9:15]
            tare_in_grams = int(tare_str)

            weight_in_kg = weight_in_grams / 100
            tare_in_kg = tare_in_grams / 100

            return weight_in_kg, tare_in_kg
        else:
            return None, None
    except Exception as e:
        print(f"Erro ao extrair peso: {e}")
        return None, None

def save_weight_to_file(weight, tare, file_name="pesos_maiores.txt"):
    try:
        with open(file_name, "a") as file:
            file.write(f"Peso: {weight:.3f} kg, Tara: {tare:.3f} kg\n")
        print(f"Peso {weight:.3f} kg e Tara {tare:.3f} kg salvos no arquivo.")
    except Exception as e:
        print(f"Erro ao salvar o peso no arquivo: {e}")
        
# Thread para leitura da porta serial
def serial_read_thread():
    global peso_atual, estado, running
    try:
        ser = serial.Serial(
            port="COM5",
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
        )
        print("Conectado à porta COM5. Aguardando dados...")

        while running:
            if ser.in_waiting > 0:
                raw_data = ser.read_all()
                process_serial_data(raw_data)
            time.sleep(0.1)

    except serial.SerialException as e:
        print(f"Erro ao acessar a porta serial: {e}")
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()

# Função para processar dados
def process_serial_data(raw_data):
    global peso_atual, estado, vlr_final
    try:
        decoded_data = raw_data.decode("utf-8", errors="ignore")
        messages = decoded_data.split("\x02")
        peso_com_bandeja = mocked_data.get("peso_bandeja") + mocked_data.get("peso_padrao")
        peso_maximo = peso_com_bandeja + (peso_com_bandeja * mocked_data.get("taxa_maxima") / 100)
        peso_minimo = peso_com_bandeja + (peso_com_bandeja * mocked_data.get("taxa_minima") / 100)

        for message in messages:
            message = message.strip()
            if message:
                weight, tare = extract_weight(message)
                if weight is not None:
                    peso_atual = weight
                    if peso_minimo <= weight <= peso_maximo:
                        estado = "dentro"
                        vlr_final = weight
                    elif weight < peso_minimo:
                        estado = "abaixo"
                    elif weight > peso_maximo:
                        estado = "acima"

                    if vlr_final > 0 and weight is not None and weight < 1:
                        print(f"------------------------")
                        print(f"Peso final: {vlr_final:.3f} kg")
                        save_weight_to_file(vlr_final, tare)
                        vlr_final = 0

    except Exception as e:
        print(f"Erro ao processar dados da porta serial: {e}")

# Rota principal
@app.route("/")
def index():
    return render_template('index.html')

# Rota para retornar peso atual via JSON
@app.route("/peso_atual")
def peso_atual_route():
    global peso_atual, estado
    return jsonify({'peso': round(peso_atual, 2), 'estado': estado})

# Inicia a thread antes de rodar o Flask
serial_thread = threading.Thread(target=serial_read_thread, daemon=True)
serial_thread.start()

# Roda o Flask
if __name__ == "__main__":
    try:
        app.run(debug=True, use_reloader=False)
    except KeyboardInterrupt:
        running = False
        print("Encerrando o servidor e a thread...")
