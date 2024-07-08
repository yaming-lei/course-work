import requests
import json

JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiIwNjZkMjg0ZS1lNTY3LTRmMWMtYjIwNS1hZDAzZWUxZDc2MjIiLCJlbWFpbCI6IjQ5MTg5MTA0OEBxcS5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGluX3BvbGljeSI6eyJyZWdpb25zIjpbeyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJGUkExIn0seyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJOWUMxIn1dLCJ2ZXJzaW9uIjoxfSwibWZhX2VuYWJsZWQiOmZhbHNlLCJzdGF0dXMiOiJBQ1RJVkUifSwiYXV0aGVudGljYXRpb25UeXBlIjoic2NvcGVkS2V5Iiwic2NvcGVkS2V5S2V5IjoiYjA4OWYwYjE3NzJiODBkNWNkMmIiLCJzY29wZWRLZXlTZWNyZXQiOiJhYWY4MzFlYWQ5ODI2YWM1ZmEyYzM0NzVkYmJhNjc0ZThmZjIyNTZmMGQzZDU0ZWRlN2RiNTFhODU1ZDJjODdmIiwiZXhwIjoxNzUxOTg1NjU2fQ.wpiYbRuhMR4FHbDbZifTeKwqyjn6MyQQthHx4_JiPAM"
pinata_url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
	#YOUR CODE HERE
	headers = {
		'Authorization': f'Bearer {JWT}',
		'Content-Type': 'application/json'
	}
	response = requests.post(pinata_url, json=data, headers=headers)
	if response.status_code == 200:
		cid = response.json()['IpfsHash']
		return cid
	else:
		raise Exception(f"Failed to pin data to IPFS: {response.text}")


def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	#YOUR CODE HERE
	response = requests.get(f'https://gateway.pinata.cloud/ipfs/{cid}')
	if response.status_code != 200:
		raise Exception(
			f"Failed to get data from IPFS: {response.status_code} - {response.text}")

	if content_type == "json":
		try:
			data = response.json()
			if not isinstance(data, dict):
				raise TypeError("Expected a dictionary in JSON response")
			return data
		except json.JSONDecodeError:
			raise ValueError("Failed to decode JSON content from IPFS")
	else:
		raise ValueError(f"Unsupported content type: {content_type}")

