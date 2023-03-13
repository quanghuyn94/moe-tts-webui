import requests
import pyaudio

response = requests.post("http://localhost:7860/run/generation", json={
	"data": [
		"こんにちは、どうなされました？",
		1,
		0,
		False,
	]
}).json()

data = response["data"]
audio = data[1]
rate = int(data[0])

import base64

# Chuỗi dữ liệu audio ở dạng base64
audio_data_base64 = audio

# Tách phần dữ liệu base64 từ chuỗi
audio_data_base64 = audio_data_base64.split(",")[1]

# Giải mã chuỗi base64 thành dữ liệu nhị phân
audio_data = base64.decodebytes(audio_data_base64.encode())

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate, output=True)
stream.write(audio_data)
stream.stop_stream()
stream.close()
p.terminate()