import websockets
import asyncio
import pymysql
import json
import base64
import hmac
import hashlib
import datetime
from random import randrange as rand


conectados = set()

class jogo:
	def __init__(self):
		self.todas = {}
		self.iniciado = True
		self.lista1 = []
		self.lista2 = []
		self.lista3 = []

	async def servidor(self, websocket, path):
		try:
			conectados.add(websocket)

			async for message in websocket:
				await self.entradas(message, websocket)
		finally:
			conectados.remove(websocket)

	async def main_jogo(self):
		while True:
			await asyncio.sleep(7)

			if self.iniciado:
				n = rand(1, 4)

				await self.send_message_for_all(json.dumps({
					"status": 3,
					"bau_vencedor": n
				}))

				self.lista1 = []
				self.lista2 = []
				self.lista3 = []
				self.todas = {}

				status = json.dumps({
					"status": 2,
					"message": "finalizado"
				})

				self.iniciado = False
			else:
				status = json.dumps({
					"status": 1,
					"message": "iniciado"
				})

				self.iniciado = True

			await self.send_message_for_all(status)

	async def entradas(self, client_message, websocket):
		try:
			json_click = json.loads(client_message)
			jwt_payload = self.valida_jwt(json_click["token"])
		except:
			return

		if self.iniciado:
			if jwt_payload:
				uid = jwt_payload["id"]

				dados = self.mysqlc(f"SELECT * FROM usuarios WHERE uid = '{uid}'")

				if 1 == 1:#dados[2] >= saldo_apostado:#saldo fake mudar isso dps
					saldo_apostado = 0.0

					#perder saldo

					if json_click["box"] == 1:
						self.lista1.append({
							"nick": dados[3],
							"valor": saldo_apostado
						})

					elif json_click["box"] == 2:
						self.lista2.append({
							"nick": dados[3],
							"valor": saldo_apostado
						})

					elif json_click["box"] == 3:
						self.lista3.append({
							"nick": dados[3],
							"valor": saldo_apostado
						})

					self.todas = json.dumps({
						"bau_1": self.lista1,
						"bau_2": self.lista2,
						"bau_3": self.lista3
					})

					await self.send_message_for_all(self.todas)

				else:
					await websocket.send(json.dumps({"status":4,"message":"saldo insuficiente"}))
			else:
				await websocket.send(json.dumps({"status":5,"message":"token expirado"}))
		else:
			await websocket.send(json.dumps({"status":6,"message":"apostas estão encerradas"}))

	async def send_message_for_all(self, status):
		for user in conectados:
			await user.send(status)

	def valida_jwt(self, jwt):
		secret_key = 'e6fc3b775072e3bf1e3fc2cfd7f87e9ce4c9701ae6fc3b775072e3bf1e3fc2cfd7f87e9ce4c9701a'
		b64_header, b64_payload, b64_signature = jwt.split('.')
		b64_signature_checker = base64.urlsafe_b64encode(
			hmac.new(
				key=secret_key.encode(),
				msg=f'{b64_header}.{b64_payload}'.encode(),
				digestmod=hashlib.sha256
			).digest()
		).decode()

		if b64_signature_checker != b64_signature: return False
		if int(datetime.datetime.now().timestamp()) > int(json.loads(base64.b64decode(b64_payload))["exp"]): return False
	    
		return json.loads(base64.urlsafe_b64decode(b64_payload))

	def mysqlc(self, query, save=False):
		con = pymysql.connect(host="localhost", user="root", password="Isawan132!", database="site")
		cursor = con.cursor()
		cursor.execute(query)

		if not save:
			return cursor.fetchone()

		con.commit()
		return True

			
async def main():
	global jogo

	jogo = jogo()

	task1 = asyncio.ensure_future(websockets.serve(jogo.servidor, "localhost", 8765))
	task2 = asyncio.create_task(jogo.main_jogo())

	await asyncio.wait([task1, task2], return_when=asyncio.ALL_COMPLETED)

asyncio.run(main())


# verficar saldo