import sys
from datetime import datetime
from collections import Counter

LOG_FILE = "access.log" 

def get_target_date():
    if len(sys.argv) == 1:
        return None
    for flag in sys.argv[1:]:
        if flag.startswith("--date="):
            try:
                date_str = flag.split("=")[1]
                target_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%b/%Y")
                print (f"Статистика по дате {target_date}")
                return target_date
            except ValueError:
                print ("Неверный формат даты. Ожидается --date=YYYY-mm-dd")
                sys.exit(1)

#Построчно читает лог из access.log
def process_logs(target_date):
    ip_counter = Counter ()
    methods_counter = Counter ()
    error_count = 0
    matched_lines = 0
    try:
        with open (LOG_FILE, 'r') as file, open ("errors.log", 'w') as errors:
            for line in file:
                parts = line.split()
                if len(parts) < 9:
                    continue

                if target_date and target_date not in parts[3]:
                    continue
                

                ip=parts[0]
                method=parts[5].strip('"')
                status = int(parts[8])
                ip_counter[ip] += 1
                methods_counter[method] += 1

                matched_lines += 1

                if 400 <= status < 600:
                        errors.write(line)
                        error_count += 1

        if matched_lines == 0:
            if target_date:
                print("Логи по выбранной дате не найдены.")
                sys.exit(1)
            else:
                print(f"Файл {LOG_FILE} пуст.")
                sys.exit(1) 
                    

        stats = {"methods_counter":methods_counter,
            "ip_counter": ip_counter,
            "error_count": error_count,
            "matched_lines":matched_lines}
        
        return stats
    except (FileNotFoundError):
        print (f"{LOG_FILE} не найден. Переместите файл в текущую директорию или переименуйте его в {LOG_FILE}.")
        sys.exit(1)

def print_stats(stats):
    methods_counter = stats["methods_counter"]
    ip_counter = stats ["ip_counter"]
    error_count = stats ["error_count"]
    matched_lines = stats ["matched_lines"]

    print ("=== Топ 3 IP-адреса ===")
    for ip, count in ip_counter.most_common(3):
        print (f"{ip}: {count} запросов")

    print ("=== Статистика по методам ===")
    for method, count in methods_counter.most_common():
        print (f"{method}: {count}")
    print ("=== Статистика ошибок (4xx-5xx) ===")
    print(f"Строки с ошибками записаны в файл errors.log")

def main():
    target_date = get_target_date()
    stats = process_logs(target_date)
    print_stats(stats)

if __name__ == "__main__":
    main()