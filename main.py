import serial
import time
import winsound

mocked_data = {
    "id_pedido": 1,
    "id_balanca": 1,
    "taxa_maxima": 5.0,
    "taxa_minima": 3.0,
    "peso_padrao": 2.0,
    "peso_bandeja": 0.8,
}

vlr_final = 0

def extract_weight(data):
    try:
        if len(data) >= 13 and data.startswith("<q") or data.startswith("<p"):
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

def process_serial_data(raw_data):
    global vlr_final
    try:
        decoded_data = raw_data.decode('utf-8', errors='ignore')
        messages = decoded_data.split('\x02')
        peso_com_bandeja = mocked_data.get("peso_bandeja") + mocked_data.get("peso_padrao")            
        peso_maximo = ((peso_com_bandeja) + (peso_com_bandeja * mocked_data.get("taxa_maxima")/100))
        peso_minimo = ((peso_com_bandeja) + (peso_com_bandeja * mocked_data.get("taxa_minima")/100))
        print(f"------------------------")
        print(f"Peso mínimo: {peso_minimo:.3f} kg")
        print(f"Peso máximo: {peso_maximo:.3f} kg")

        for message in messages:
            message = message.strip()
            if message:
                weight, tare = extract_weight(message)
                if weight is not None and tare is not None: 
                    print(f"------------------------")
                    print(f"------------------------")

                    if weight >= peso_minimo and weight <= peso_maximo:
                        print(f"Peso dentro do limite: {weight:.3f} kg")
                        vlr_final = weight   
                    elif weight < peso_minimo:
                        print(f"Peso abaixo do limite mínimo: {weight:.3f} kg")
                    elif weight > peso_maximo:
                        print(f"Peso acima do limite máximo: {weight:.3f} kg")
                    else:
                        print(f"Dado inválido: {message}")
                        
                    if vlr_final > 0 and weight is not None and weight < 1:
                        print(f"------------------------")
                        print(f"Peso final: {vlr_final:.3f} kg")
                        save_weight_to_file(vlr_final, tare)
                        winsound.Beep(1000, 500)  # Som de 1000 Hz por 500 ms
                        vlr_final = 0

    except Exception as e:
        print(f"Erro ao processar dados da porta serial: {e}")

def main():
    try:
        ser = serial.Serial(
            port='COM5',
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        print(f"Conectado à porta COM5. Aguardando dados...")

        while True:
            if ser.in_waiting > 0:
                raw_data = ser.read_all()
                process_serial_data(raw_data)
            else:
                time.sleep(1)

    except serial.SerialException as e:
        print(f"Erro ao acessar a porta serial: {e}")
    except KeyboardInterrupt:
        print("\nEncerrando aplicação...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
