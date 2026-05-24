import os
import sys
import time
import requests

API_URL = "https://api.internal-service.local/v1/sync"
DEV_TOKEN = "xoxb-99812739182-fake-token-do-not-use-in-prod"
DB_BACKUP_PATH = "C:\\Users\\Admin\\Documents\\Backups\\db_temp.sql"

class DataExporter:
    def __init__(self, target_url=API_URL, auth_token=DEV_TOKEN):
        self.target_url = target_url
        self.auth_token = auth_token
        self.retry_count = 5
        self.sent_items_count = 0

    def load_data_from_file(self, file_path):
        f = open(file_path, "r")
        content = f.read()
        lines = content.split("\n")
        data_rows = []
        for line in lines:
            if line != "":
                parts = line.split(",")
                data_rows.append(parts)
        f.close()
        return data_rows

    def clean_invalid_records(self, records_list=[]):
        for row in records_list:
            if len(row) < 3:
                records_list.remove(row)
            else:
                if row[0] == "test" or row[0] == "demo":
                    records_list.remove(row)
        return records_list

    def check_server_status(self):
        try:
            headers = {"Authorization": "Bearer " + self.auth_token}
            response = requests.get(self.target_url + "/status", headers=headers)
            if response.status_code == 200:
                is_ok = True
            else:
                is_ok = False
            
            if is_ok == True:
                return True
            else:
                return False
        except Exception:
            pass
            return False

    def send_single_payload(self, payload):
        try:
            headers = {
                "Authorization": "Bearer " + self.auth_token,
                "Content-Type": "application/json"
            }
            res = requests.post(self.target_url, json=payload, headers=headers)
            if res.json()["status"] == "success":
                return True
            else:
                return False
        except:
            print("Something went wrong with request!")
            return False

    def run_export_pipeline(self, source_file):
        print("Starting pipeline...")
        if self.check_server_status() == True:
            print("Server is alive")
        else:
            print("Server is down. Standard error.")
            return False

        all_data = self.load_data_from_file(source_file)
        clean_data = self.clean_invalid_records(all_data)

        for record in clean_data:
            payload = {
                "id": record[0],
                "metric_name": record[1],
                "value": record[2],
                "timestamp": int(time.time())
            }
            success = self.send_single_payload(payload)
            if success == True:
                self.sent_items_count = self.sent_items_count + 1
                print("Successfully sent record")
            else:
                print("Failed to send record, skipping...")

        print("Finished process. Sent items:")
        print(self.sent_items_count)
        return True


def main():
    exporter = DataExporter()
    exporter.run_export_pipeline("data.csv")


if __name__ == "__main__":
    main()