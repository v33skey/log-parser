import pytest
from unittest.mock import patch, mock_open
from parser import get_target_date, process_logs
import os
import subprocess
from pathlib import Path
import shutil

#проверяем функцию преобразования даты
def test_get_target_date_valid():
    test_args = ["parser.py", "--date=2026-02-16"]
    with patch("sys.argv", test_args):
        result = get_target_date()
        assert result == "16/Feb/2026"

#проверка корректности работы скрипта, если не был указан флаг с датой
def test_get_target_date_none():
    test_args = ["parser.py"]
    with patch("sys.argv", test_args):
        result = get_target_date()
        assert result is None

#проверка на отсутствие файла access.log
def test_process_logs_no_file():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(SystemExit) as e:
            process_logs("16/Feb/2026")
        assert e.value.code == 1

#проверка функционала завершения исполнения кода, если файл access.log пуст
def test_process_logs_empty_file():
    with patch("builtins.open", mock_open(read_data="")):
        with pytest.raises(SystemExit) as e:
            process_logs(None)
        assert e.value.code == 1

#тест логики обработки строк логов, добавлена "битая" строка для проверки, что битые строки не попадут в статистику
def test_process_logs_logic():
    fake_content = [
        '172.20.5.9 - - [16/Feb/2026:03:54:54 +0300] "GET /product/1004 HTTP/1.1" 200 6819 \n' 
        '172.16.0.7 - - [16/Feb/2026:04:01:53 +0300] "DELETE /api/cart/item/73 HTTP/1.1" 404 4812 \n'
        '192.0.2.77 - - [16/Feb/2026:04:03:11 +0300] "GET /favicon.ico HTTP/1.1" 200 307988 \n'
        '100.64.12.3 - - [16/Feb/2026:04:13:51 +0300] "GET /index.html HTTP/1.1" 404 30493 \n'
        '192.0.2.77 - - [16/Feb/2026:11:21:22 +0300]'
    ]
    fake_log_content = "\n".join(fake_content)
    with patch("builtins.open", mock_open(read_data=fake_log_content)):
        stats = process_logs("16/Feb/2026")
        
        assert stats["matched_lines"] == 4
        assert stats["error_count"] == 2  
        assert stats["ip_counter"]["192.0.2.77"] == 1
        assert stats["methods_counter"]["GET"] == 3
        assert stats["methods_counter"]["DELETE"] == 1

log_lines = [
        '1.1.1.1 - - [16/Feb/2026:03:54:54 +0300] "GET /product/1004 HTTP/1.1" 200 6819',
        '1.1.1.1 - - [16/Feb/2026:04:01:53 +0300] "DELETE /api/cart/item/73 HTTP/1.1" 404 4812',
        '2.2.2.2 - - [16/Feb/2026:04:03:11 +0300] "GET /favicon.ico HTTP/1.1" 200 307988',
        '2.2.2.2 - - [17/Feb/2026:04:13:51 +0300] "GET /index.html HTTP/1.1" 404 30493',
        '2.2.2.2 - - [16/Feb/2026:00:55:53 +0300]'
    ]
def test_bash_top_ips(tmp_path):
    (tmp_path / 'access.log').write_text('\n'.join(log_lines))
    shutil.copy(Path("parser.sh").absolute(), tmp_path / "parser.sh")

    cmd= 'bash ./parser.sh'
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=str(tmp_path))

    assert "1.1.1.1: 2 requests" in result.stdout
    assert "2.2.2.2: 2 requests" in result.stdout 

def test_bash_methods_counter(tmp_path):
    (tmp_path / 'access.log').write_text('\n'.join(log_lines))
    shutil.copy(Path("parser.sh").absolute(), tmp_path / "parser.sh")

    cmd = 'bash -c "source ./parser.sh && methods_counter"'
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=str(tmp_path))

    assert "GET: 3" in result.stdout
    assert "DELETE: 1" in result.stdout

def test_bash_error_codes(tmp_path):
    (tmp_path / 'access.log').write_text('\n'.join(log_lines))
    shutil.copy(Path("parser.sh").absolute(), tmp_path / "parser.sh")

    cmd = 'bash -c "source ./parser.sh && error_status_code"'
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=str(tmp_path))

    assert "(2 записей)" in result.stdout

def test_bash_date_filter(tmp_path):
    (tmp_path / 'access.log').write_text('\n'.join(log_lines))
    shutil.copy(Path("parser.sh").absolute(), tmp_path / "parser.sh")

    cmd = 'bash ./parser.sh --date=2026-02-17'
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=str(tmp_path))

    assert "Найдено записей за указанную дату: 1" in result.stdout