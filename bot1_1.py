import json
import os
import glob
import random
import string
import time
import msvcrt
import requests
import time
import secrets
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from queue import Queue
from threading import Thread
from datetime import datetime, timedelta
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ctypes import *

# Для Windows консоли
windll.kernel32.SetConsoleMode(windll.kernel32.GetStdHandle(-11), 7)
stdout_handle = windll.kernel32.GetStdHandle(-11)
mode = c_ulong()
windll.kernel32.GetConsoleMode(stdout_handle, byref(mode))
mode.value |= 0x0004
windll.kernel32.SetConsoleMode(stdout_handle, mode)

class AutoPublisher:
    def __init__(self):
        self.configs = {}
        self.meta_data = {}
        self.running = True
        self.running_configs = set()
        self.last_display = 0
        # Сначала загружаем конфиги
        self.load_configs()
        # Затем загружаем мета-данные с новой версией load_meta_data
        self.load_meta_data()
        os.system('cls' if os.name == 'nt' else 'clear')
        self.job_queue = Queue()
        self.worker_thread = Thread(target=self.worker, daemon=True)
        self.worker_thread.start()
        
    def load_configs(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        configs_dir = os.path.join(script_dir, 'configs')
        
        if not os.path.exists(configs_dir):
            os.makedirs(configs_dir)
        
        config_files = glob.glob(os.path.join(configs_dir, '*.json'))
        if not config_files:
            return
    
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    config_name = os.path.splitext(os.path.basename(config_file))[0]
                    
                    required_fields = ['region_id', 'name', 'email', 'place', 'age', 'style', 'body_type', 'message_file']
                    missing_fields = [field for field in required_fields if field not in config]
                    
                    if missing_fields:
                        continue
    
                    if not os.path.isabs(config['message_file']):
                        config['message_file'] = os.path.join(script_dir, config['message_file'])
                    
                    if 'photos' in config:
                        config['photos'] = [
                            os.path.join(script_dir, photo) if not os.path.isabs(photo) else photo
                            for photo in config['photos']
                        ]
    
                    if not config.get('password'):
                        config['password'] = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                    
                    if not config.get('user_agent'):
                        from fake_useragent import UserAgent
                        ua = UserAgent()
                        config['user_agent'] = ua.chrome
                    
                    if not config.get('headless'):
                        config['headless'] = 'N'
    
                    # сохраняем обновлённый конфиг
                    with open(config_file, 'w', encoding='utf-8') as f_out:
                        json.dump(config, f_out, indent=4, ensure_ascii=False)
    
                    self.configs[config_name] = config
    
            except Exception as e:
                continue

    def load_meta_data(self):
        # Инициализируем saved_meta как пустой словарь
        saved_meta = {}
        
        # Пытаемся загрузить существующие метаданные
        if os.path.exists('config_meta.json'):
            try:
                with open('config_meta.json', 'r', encoding='utf-8') as f:
                    saved_meta = json.load(f)
            except:
                pass  # Если файл поврежден, оставляем пустой словарь
    
        current_time = datetime.now()
        
        # Обрабатываем каждый конфиг
        for config_name in self.configs:
            meta = saved_meta.get(config_name, {})
            was_enabled = meta.get('enabled', False)
            
            self.meta_data[config_name] = {
                'enabled': was_enabled,
                'interval_min': meta.get('interval_min', 5),
                'interval_max': meta.get('interval_max', 7),
                'success_count': 0,  # сбрасываем на запуске
                'fail_count': 0,     # сбрасываем на запуске
                'total_success': meta.get('total_success', 0),  # сохраняем навсегда
                'total_fail': meta.get('total_fail', 0),
                'last_run_time': meta.get('last_run_time', None),
                'last_result': meta.get('last_result', None),
                'next_run_time': None
            }
            
            if was_enabled:
                interval_minutes = random.randint(
                    self.meta_data[config_name]['interval_min'],
                    self.meta_data[config_name]['interval_max']
                )
                next_run_time = current_time + timedelta(minutes=interval_minutes)
                self.meta_data[config_name]['next_run_time'] = next_run_time.isoformat()
    
        self.save_meta_data()
        
    def save_meta_data(self):
        try:
            with open('config_meta.json', 'w', encoding='utf-8') as f:
                json.dump(self.meta_data, f, indent=4)
        except Exception as e:
            print(f"Error saving meta data: {e}")
            
    def format_time_until(self, next_time: Optional[str]) -> str:
        if not next_time:
            return "---"
        try:
            next_dt = datetime.fromisoformat(next_time)
            now = datetime.now()
            if next_dt <= now:
                return "00:00:00"
            
            diff = next_dt - now
            total_seconds = int(diff.total_seconds())
            
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "---"

    def goto_xy(self, x: int, y: int):
        windll.kernel32.SetConsoleCursorPosition(stdout_handle, y * 80 + x)
            
    def display_menu(self, force_refresh=False):
        current_time = time.time()
        
        if force_refresh or (current_time - self.last_display >= 1.0):
            os.system('cls' if os.name == 'nt' else 'clear')
            current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            print("┌" + "─"*87 + "┐")
            print("│" + f"Auto Publisher - Current Time: {current_time_str}".center(87) + "│")
            print("├" + "─"*87 + "┤")
            print("│ {:<15} │ {:<6} │ {:<8} │ {:<12} │ {:<5} │ {:<5} │ {:<9} │ {:<4} │".format(
                "Config Name", "Status", "Next In", "Last Run", "OK", "FAIL", "OK/FAIL", "Head"
            ))
            print("├" + "─"*87 + "┤")
        
            row = 5
            for config_name in sorted(self.configs.keys()):
                meta = self.meta_data[config_name]
                config = self.configs[config_name]
                status = "ON" if meta['enabled'] else "OFF"
                next_in = self.format_time_until(meta['next_run_time'])
                headless = "Y" if config.get('headless', 'N').upper() == 'Y' else "N"
                
                last_run = "Never"
                if meta['last_run_time']:
                    result = "OK" if meta['last_result'] else "FAIL"
                    last_run = result
                
                print("│ {:<15} │ {:<6} │ {:<8} │ {:<12} │ {:<5} │ {:<5} │ {:<9} │ {:<4} │".format(
                    config_name[:15], status, next_in, last_run,
                    meta['success_count'], meta['fail_count'],
                    f"{meta.get('total_success', 0)}/{meta.get('total_fail', 0)}", headless
                ))
                row += 1
        
            print("└" + "─"*87 + "┘\n")
            print("[1] Toggle config | [2] Set interval | [3] Force run | [4] Quit")
            print("[5] Kill drivers | [6] Toggle headless")
            print("> ", end='', flush=True)
            
            self.last_display = current_time
        
    def process_config(self, config_name):
        driver = None
        try:
            config = self.configs[config_name]
            chrome_options = webdriver.ChromeOptions()
            script_dir = os.path.dirname(os.path.abspath(__file__))
            profile_path = os.path.join(script_dir, 'cookies', config_name, 'profile')
            os.makedirs(profile_path, exist_ok=True)
    
            # Настройки браузера как в bot20.py
            chrome_options.add_argument(f'--user-data-dir={profile_path}')
            chrome_options.add_argument('--lang=ja')
            chrome_options.add_argument('--accept-language=ja-JP')
            chrome_options.add_experimental_option("prefs", {
                "profile.exit_type": "Normal",
                "profile.default_content_setting_values.notifications": 2,
                "profile.background_mode.enabled": False,
                "exit_type": "Normal"
            })
    
            if config.get('user_agent'):
                chrome_options.add_argument(f'--user-agent={config["user_agent"]}')
    
            if config.get('headless', 'N').upper() == 'Y':
                chrome_options.add_argument('--headless=new')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--window-size=1920,1080')
    
            service = Service(os.path.join(script_dir, 'chromedriver.exe'))
            service.log_path = os.devnull
    
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get(f'https://oshioki24.com/board/post/{config["region_id"]}/')
    
            max_attempts = 5
            attempt = 0
            consecutive_fails = self.meta_data[config_name].get('consecutive_fails', 0)
    
            # Первая попытка - заполняем все поля
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, 'FB'))
            )
    
            # Заполняем основные поля
            fields = {
                'name': config['name'],
                'mailaddress': config['email'],
                'password': config['password']
            }
            for field, value in fields.items():
                element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.NAME, field))
                )
                element.clear()
                element.send_keys(value)
                time.sleep(random.uniform(0.2, 0.7))
    
            # Заполняем селекты
            selects = {
                'place': config['place'],
                'age': config['age'],
                'sex': config['style'],
                'figure': config['body_type']
            }
            for field, value in selects.items():
                element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.NAME, field))
                )
                Select(element).select_by_value(value)
                time.sleep(random.uniform(0.3, 1.0))
    
            # Заполняем сообщение через JavaScript
            with open(config['message_file'], 'r', encoding='utf-8') as f:
                message = f.read()
            escaped_message = message.replace("'", "\\'").replace("\n", "\\n")
            message_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, 'message'))
            )
            driver.execute_script(f"arguments[0].value = '{escaped_message}';", message_element)
    
            # Загрузка фото
            for i, photo_path in enumerate(config.get('photos') or [], 1):
                if photo_path and photo_path.strip():
                    abs_photo_path = os.path.abspath(photo_path)
                    photo_input = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.NAME, f'photo{i}'))
                    )
                    photo_input.send_keys(abs_photo_path)
                    WebDriverWait(driver, 15).until(
                        lambda d: photo_input.get_attribute('value') != ''
                    )
    
            while attempt < max_attempts:
                try:
                    # Получаем новый FB value при каждой попытке
                    fb_value = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.NAME, 'FB'))
                    ).get_attribute('value')
    
                    if attempt > 0:
                        # При повторных попытках обновляем только пароль и фото
                        password_field = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.NAME, 'password'))
                        )
                        password_field.clear()
                        password_field.send_keys(config['password'])
                        time.sleep(random.uniform(0.5, 1.5))
    
                        for i, photo_path in enumerate(config.get('photos') or [], 1):
                            if photo_path and photo_path.strip():
                                abs_photo_path = os.path.abspath(photo_path)
                                photo_input = WebDriverWait(driver, 15).until(
                                    EC.presence_of_element_located((By.NAME, f'photo{i}'))
                                )
                                photo_input.send_keys(abs_photo_path)
                                WebDriverWait(driver, 15).until(
                                    lambda d: photo_input.get_attribute('value') != ''
                                )
    
                    # Получаем токен reCAPTCHA
                    WebDriverWait(driver, 25).until(
                        lambda d: d.execute_script('return typeof grecaptcha !== "undefined"')
                    )
                    
                    recaptcha_token = driver.execute_script("""
                        return new Promise((resolve) => {
                            grecaptcha.ready(function() {
                                grecaptcha.execute('6Ld2UMMUAAAAAHrjnIJST8wcfUdolcKR7rPH2Fmu', {
                                    action: 'submit'
                                }).then(function(token) {
                                    resolve(token);
                                });
                            });
                        });
                    """)
    
                    # Устанавливаем токены
                    driver.execute_script(f"""
                        document.getElementById('GRR').value = '{recaptcha_token}';
                        document.getElementById('FB').value = '{fb_value}';
                    """)
    
                    # Отправляем форму
                    submit_button = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.ID, 'form-submit'))
                    )
                    submit_button.click()
    
                    # Ждем результат
                    WebDriverWait(driver, 20).until(
                        lambda d: '投稿ありがとうございました' in d.page_source or 
                                '認証に失敗しました' in d.page_source
                    )
    
                    if '投稿ありがとうございました' in driver.page_source:
                        # Сбрасываем счетчик последовательных неудач
                        self.meta_data[config_name]['consecutive_fails'] = 0
                        self.save_meta_data()
                        return True
    
                    if '認証に失敗しました' in driver.page_source:
                        attempt += 1
                        if attempt == max_attempts:
                            # Увеличиваем счетчик последовательных неудач
                            consecutive_fails += 1
                            self.meta_data[config_name]['consecutive_fails'] = consecutive_fails
    
                            # Определяем таймаут для следующей попытки
                            if consecutive_fails == 1:
                                # Первая серия неудач - без таймаута
                                pass
                            elif consecutive_fails == 2:
                                # Вторая серия - 5 минут
                                self.meta_data[config_name]['next_run_time'] = (
                                    datetime.now() + timedelta(minutes=5)
                                ).isoformat()
                            elif consecutive_fails == 3:
                                # Третья серия - 15 минут
                                self.meta_data[config_name]['next_run_time'] = (
                                    datetime.now() + timedelta(minutes=15)
                                ).isoformat()
                            else:
                                # Четвертая и последующие - 30 минут
                                self.meta_data[config_name]['next_run_time'] = (
                                    datetime.now() + timedelta(minutes=30)
                                ).isoformat()
                            
                            self.save_meta_data()
                            return False
    
                        time.sleep(random.uniform(1, 2))
                        continue
    
                except Exception as e:
                    print(f"[ERROR] Attempt {attempt + 1}: {str(e)}")
                    attempt += 1
                    if attempt == max_attempts:
                        return False
                    time.sleep(random.uniform(1, 2))
                    continue
    
            return False
    
        except Exception as e:
            print(f"[ERROR process_config] {config_name}: {e}")
            return False
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def preview_config(self, config_name):
        try:
            config = self.configs[config_name]

            chrome_options = webdriver.ChromeOptions()
            script_dir = os.path.dirname(os.path.abspath(__file__))
            profile_path = os.path.join(script_dir, 'cookies', config_name, 'profile')
            os.makedirs(profile_path, exist_ok=True)

            chrome_options.add_argument(f'--user-data-dir={profile_path}')
            chrome_options.add_argument('--lang=ja')
            chrome_options.add_argument('--accept-language=ja-JP')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

            if config.get('user_agent'):
                chrome_options.add_argument(f'--user-agent={config["user_agent"]}')

            chromedriver_path = os.path.join(script_dir, 'chromedriver.exe')
            service = Service(chromedriver_path, log_path='NUL')
            service.creationflags = 0x08000000

            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get(f'https://oshioki24.com/board/post/{config["region_id"]}/')

            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, 'FB'))
            )

            fields = {
                'name': config['name'],
                'mailaddress': config['email'],
                'password': config['password']
            }

            for field, value in fields.items():
                element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.NAME, field))
                )
                element.clear()
                element.send_keys(value)
                time.sleep(random.uniform(0.2, 0.6))

            selects = {
                'place': config['place'],
                'age': config['age'],
                'sex': config['style'],
                'figure': config['body_type']
            }

            for field, value in selects.items():
                element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.NAME, field))
                )
                Select(element).select_by_value(value)
                time.sleep(random.uniform(0.2, 0.6))

            with open(config['message_file'], 'r', encoding='utf-8') as f:
                message = f.read()

            message_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, 'message'))
            )
            message_element.clear()
            message_element.send_keys(message)

            for i, photo_path in enumerate(config.get('photos', []), 1):
                if photo_path and photo_path.strip():
                    abs_photo_path = os.path.abspath(photo_path)
                    photo_input = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.NAME, f'photo{i}'))
                    )
                    photo_input.send_keys(abs_photo_path)
                    WebDriverWait(driver, 15).until(
                        lambda d: photo_input.get_attribute('value') != ''
                    )

            while driver.service.process.poll() is None:
                time.sleep(1)


        except Exception as e:
            print(f"[ERROR preview_config] {e}")

    def force_close_all_webdrivers(self):
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'chromedriver.exe' or \
                   (proc.info['name'] == 'chrome.exe' and 
                    proc.info['cmdline'] and 
                    '--remote-debugging-port=' in ' '.join(proc.info['cmdline'])):
                    proc.kill()
            except:
                continue
                
    def start_browser_timer(self, driver):
        def check_and_close():
            time.sleep(300)  # 5 минут
            try:
                driver.quit()
            except:
                pass
        
        Thread(target=check_and_close, daemon=True).start()

    def handle_menu_choice(self, ch):  # Добавляем параметр ch
        if ch == b'4':
            print("\nExiting...")
            os._exit(0)
        elif ch == b'5':
            self.force_close_all_webdrivers()
            self.display_menu(force_refresh=True)
            return
        elif ch == b'1':
            print("\nSelect config number:")
            configs = list(sorted(self.configs.keys()))
            for i, name in enumerate(configs, 1):
                print(f"{i}. {name}")
            
            try:
                config_num = int(input("\nEnter number (or 0 to return): "))
                if 0 < config_num <= len(configs):
                    config_name = configs[config_num-1]
                    self.meta_data[config_name]['enabled'] = not self.meta_data[config_name]['enabled']
                    if self.meta_data[config_name]['enabled']:
                        interval_minutes = random.randint(
                            self.meta_data[config_name]['interval_min'],
                            self.meta_data[config_name]['interval_max']
                        )
                        next_run_time = datetime.now() + timedelta(minutes=interval_minutes)
                        self.meta_data[config_name]['next_run_time'] = next_run_time.isoformat()
                    else:
                        self.meta_data[config_name]['next_run_time'] = None
                    self.save_meta_data()
            except:
                pass
                
        elif ch == b'2':
            print("\nSelect config number:")
            configs = list(sorted(self.configs.keys()))
            for i, name in enumerate(configs, 1):
                print(f"{i}. {name}")
            
            try:
                config_num = int(input("\nEnter number (or 0 to return): "))
                if 0 < config_num <= len(configs):
                    config_name = configs[config_num-1]
                    print(f"\nCurrent interval: {self.meta_data[config_name]['interval_min']}-{self.meta_data[config_name]['interval_max']} minutes")
                    min_val = int(input("\nEnter new minimum interval (0 or more minutes): "))
                    if min_val >= 0:
                        max_val = int(input("Enter new maximum interval (must be >= minimum): "))
                        if max_val >= min_val:
                            self.meta_data[config_name]['interval_min'] = min_val
                            self.meta_data[config_name]['interval_max'] = max_val
                            self.save_meta_data()
            except:
                pass
                
        elif ch == b'3':
            print("\nSelect config number:")
            configs = list(sorted(self.configs.keys()))
            for i, name in enumerate(configs, 1):
                print(f"{i}. {name}")
            
            try:
                config_num = int(input("\nEnter number (or 0 to return): "))
                if 0 < config_num <= len(configs):
                    config_name = configs[config_num-1]
                    Thread(target=self.preview_config, args=(config_name,), daemon=True).start()
                    return
            except:
                pass
                
        elif ch == b'6':
            print("\nSelect config number:")
            configs = list(sorted(self.configs.keys()))
            for i, name in enumerate(configs, 1):
                print(f"{i}. {name}")
            
            try:
                config_num = int(input("\nEnter number (or 0 to return): "))
                if 0 < config_num <= len(configs):
                    config_name = configs[config_num-1]
                    current = self.configs[config_name].get('headless', 'N').upper()
                    self.configs[config_name]['headless'] = 'N' if current == 'Y' else 'Y'
                    self._save_config(config_name, self.configs[config_name])
            except:
                pass

        self.display_menu(force_refresh=True)
            
    def check_and_run_configs(self):
        current_time = datetime.now()
    
        for config_name, meta in self.meta_data.items():
            if not meta.get('enabled', False):
                continue
    
            if meta.get('is_updating', False) or \
               config_name in self.running_configs or \
               config_name in list(self.job_queue.queue):
                continue
    
            next_run_time = meta.get('next_run_time')
            if next_run_time:
                next_run_time = datetime.fromisoformat(next_run_time)
            else:
                next_run_time = current_time
    
            if current_time >= next_run_time:
                self.job_queue.put(config_name)
                
    def decode_email(self, encoded_string):
        try:
            encoded_string = encoded_string.strip()
            coded_chars = []
            for i in range(0, len(encoded_string), 2):
                coded_chars.append(int(encoded_string[i:i+2], 16))
            key = coded_chars[0]
            email = ""
            for i in range(1, len(coded_chars)):
                email += chr(coded_chars[i] ^ key)
            return email if '@' in email else None
        except:
            return None
    
    def update_token(self, config_name):
        config = self.configs[config_name]
        target_email = config['email']
        region_id = config['region_id']
        
        print(f"[Token Update] Starting token update for {config_name}")
        
        for _ in range(10):
            try:
                # Добавляем уникальные параметры для идентификации
                headers = {
                    'User-Agent': config['user_agent'],
                    'X-Config-Identifier': f"{config_name}-{datetime.now().timestamp()}"
                }
                url = f'https://oshioki24.com/board/{region_id}/'
                response = requests.get(url, headers=headers, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')
                panels = soup.find_all('div', class_='panel panel-default panel-board')
                
                for panel in panels:
                    email_link = panel.find('div', class_='panel-head').find('a')
                    if not email_link:
                        continue
                    href = email_link.get('href', '')
                    
                    if '/cdn-cgi/l/email-protection#' in href:
                        protection_code = href.split('#')[-1]
                        decrypted_email = self.decode_email(protection_code)
                        
                        if decrypted_email == target_email:
                            report_button = panel.find('button', class_='modal-report-open')
                            if report_button:
                                new_token = report_button.get('id')
                                if new_token:
                                    config['token'] = new_token
                                    self._save_config(config_name, config)
                                    return True
                time.sleep(15)
            except Exception as e:
                print(f"Token update error: {str(e)}")
                time.sleep(15)
        return False
        
    def _save_config(self, config_name, config_data):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'configs', f'{config_name}.json')
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        # Обновляем кэш конфигурации
        self.configs[config_name] = config_data

    def _run_config(self, config_name):
        try:
            current_time = datetime.now()
            result = self.process_config(config_name)
            meta = self.meta_data[config_name]
    
            # Базовые интервалы
            base_min = meta['interval_min']
            base_max = meta['interval_max']
    
            # Создаём уникальный генератор
            rng = random.SystemRandom()
            interval_minutes = rng.randint(base_min, base_max)
            interval_seconds = rng.randint(0, 59)
    
            next_run_time = current_time + timedelta(
                minutes=interval_minutes,
                seconds=interval_seconds
            )
            meta['next_run_time'] = next_run_time.isoformat()
    
            meta['last_run_time'] = current_time.isoformat()
            meta['last_result'] = result
            meta['is_updating'] = False
    
            if result:
                meta['success_count'] += 1
                meta['total_success'] += 1
                # После успешной публикации обновляем токен
                self.update_token(config_name)
            else:
                meta['fail_count'] += 1
                meta['total_fail'] += 1
    
            self.save_meta_data()
            self.display_menu(force_refresh=True)
    
        except Exception as e:
            print(f"[ERROR _run_config] {e}")
            meta = self.meta_data.get(config_name, {})
            meta['is_updating'] = False
            self.save_meta_data()
            
    def worker(self):
        while self.running:
            config_name = self.job_queue.get()
            self.running_configs.add(config_name)
            try:
                self._run_config(config_name)
            except Exception as e:
                print(f"[ERROR] Ошибка в конфиге {config_name}: {e}")
            finally:
                self.running_configs.remove(config_name)
                self.job_queue.task_done()

    def run(self):
        self.display_menu(force_refresh=True)
        
        while self.running:
            try:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if ch in [b'1', b'2', b'3', b'4', b'5', b'6']:
                        self.handle_menu_choice(ch)  # Передаём ch в handle_menu_choice
                
                self.display_menu()
                
                if self.check_and_run_configs():
                    self.display_menu(force_refresh=True)
                    
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                os._exit(0)
            except Exception:
                time.sleep(0.1)
                
if __name__ == "__main__":
    publisher = AutoPublisher()
    publisher.run()