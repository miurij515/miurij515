import os
import sys
import time
import json
import glob
import random
import shutil
import string
import tempfile
import requests
from datetime import datetime, timedelta

# third-party
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pytz
from rich.console import Console 
from rich.panel import Panel
from rich.prompt import Prompt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import threading
import re

console = Console()

#2. Глобальные переменные и константы
REGIONS_WITH_POPULATION = {
    "1": {
        "name": "Hokkaido",
        "population": 5224614,
        "places": {
            "51": {"name": "Central Hokkaido", "population": 2154578},
            "52": {"name": "South Hokkaido", "population": 347615},
            "53": {"name": "North Hokkaido", "population": 334940},
            "54": {"name": "East Hokkaido", "population": 327710}
        }
    },
    "2": {
        "name": "Tohoku",
        "population": 8548167,
        "places": {
            "2": {"name": "Aomori", "population": 1204392},
            "5": {"name": "Akita", "population": 929901},
            "3": {"name": "Iwate", "population": 1180595},
            "6": {"name": "Yamagata", "population": 1041025},
            "7": {"name": "Fukushima", "population": 1790181},
            "4": {"name": "Miyagi", "population": 2279977}
        }
    },
    "3": {
        "name": "Kanto",
        "population": 42596719,
        "places": {
            "13": {"name": "Tokyo", "population": 14049146},
            "14": {"name": "Kanagawa", "population": 9262118},
            "11": {"name": "Saitama", "population": 7344765},
            "12": {"name": "Chiba", "population": 6278060},
            "8": {"name": "Ibaraki", "population": 2839555},
            "10": {"name": "Gunma", "population": 1913254},
            "9": {"name": "Tochigi", "population": 1908821}
        }
    },
    "5": {
        "name": "Hokuriku-Koshinetsu",
        "population": 8861076,
        "places": {
            "15": {"name": "Niigata", "population": 2152693},
            "20": {"name": "Nagano", "population": 2019993},
            "16": {"name": "Toyama", "population": 1016534},
            "17": {"name": "Ishikawa", "population": 1117637},
            "18": {"name": "Fukui", "population": 752855},
            "19": {"name": "Yamanashi", "population": 801874}
        }
    },
    "6": {
        "name": "Tokai",
        "population": 14852533,
        "places": {
            "23": {"name": "Aichi", "population": 7326176},
            "22": {"name": "Shizuoka", "population": 3582297},
            "21": {"name": "Gifu", "population": 1945763},
            "24": {"name": "Mie", "population": 1742174}
        }
    },
    "7": {
        "name": "Kinki",
        "population": 20768655,
        "places": {
            "27": {"name": "Osaka", "population": 8778035},
            "28": {"name": "Hyogo", "population": 5469762},
            "26": {"name": "Kyoto", "population": 2549749},
            "25": {"name": "Shiga", "population": 1408931},
            "29": {"name": "Nara", "population": 1305812},
            "30": {"name": "Wakayama", "population": 903265}
        }
    },
    "8": {
        "name": "Chugoku",
        "population": 7809822,
        "places": {
            "34": {"name": "Hiroshima", "population": 2759500},
            "33": {"name": "Okayama", "population": 1862317},
            "35": {"name": "Yamaguchi", "population": 1313403},
            "32": {"name": "Shimane", "population": 657909},
            "31": {"name": "Tottori", "population": 543620}
        }
    },
    "9": {
        "name": "Shikoku",
        "population": 3920103,
        "places": {
            "38": {"name": "Ehime", "population": 1306486},
            "37": {"name": "Kagawa", "population": 934060},
            "36": {"name": "Tokushima", "population": 703852},
            "39": {"name": "Kochi", "population": 675705}
        }
    },
    "10": {
        "name": "Kyushu-Okinawa",
        "population": 14511528,
        "places": {
            "40": {"name": "Fukuoka", "population": 5116046},
            "43": {"name": "Kumamoto", "population": 1718327},
            "46": {"name": "Kagoshima", "population": 1562662},
            "42": {"name": "Nagasaki", "population": 1283128},
            "44": {"name": "Oita", "population": 1106831},
            "45": {"name": "Miyazaki", "population": 1052338},
            "47": {"name": "Okinawa", "population": 1468318},
            "41": {"name": "Saga", "population": 800787}
        }
    }
}

AGE_OPTIONS = {
    "1": "18-24",
    "2": "25-34",
    "3": "35-44",
    "4": "+45"
}

STYLE_OPTIONS = {
    "1": "Fully cross-dressed",
    "2": "Cross-dressed below the neck",
    "3": "Cross-dressed in underwear",
    "4": "Transsexual",
    "5": "Man",
    "6": "Woman"
}

BODY_TYPE_OPTIONS = {
    "1": "Normal",
    "2": "Skinny",
    "3": "Skinny",
    "4": "Chubby",
    "5": "Chubby",
    "6": "Muscular",
    "7": "Slim and muscular",
    "8": "Muscular"
}

JST = pytz.timezone('Asia/Tokyo')
MIN_SCAN_INTERVAL = 60  # Минимальный интервал - 1 минута
MAX_SCAN_INTERVAL = 900  # Максимальный интервал - 15 минут
BOARDS = [1, 2, 3, 5, 6, 7, 8, 9, 10]
BASE_URL = "https://oshioki24.com/board/"
LOG_DIR = "logs"

#2. Вспомогательные функции общего назначения

def get_config_name(config_path):
    """Получает имя конфига из его пути"""
    return os.path.splitext(os.path.basename(config_path))[0]

def clear_console():
    """Очистка консоли"""
    os.system('cls' if os.name == 'nt' else 'clear')
	
def decode_email(encoded_string):
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
		
def create_temp_text_file(filename):
    """Создание и работа с временным текстовым файлом"""
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, filename)
    
    # Создаем пустой файл
    with open(temp_path, 'w', encoding='utf-8') as f:
        pass
    
    # Открываем для редактирования
    os.system(f'notepad "{temp_path}"')
    
    try:
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
    except:
        content = ''
        
    try:
        os.remove(temp_path)
    except:
        pass
        
    return content

def handle_photo_upload():
    """Обработка загрузки фотографий"""
    # Получаем путь к директории скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    photo_dir = os.path.join(script_dir, "photo")

    while True:
        temp_dir = tempfile.mkdtemp()
        os.system(f"start {temp_dir}")
        print("\nОткрыта временная папка для фотографий.")
        print("Скопируйте до 3 фотографий (jpg/png/gif, до 2MB)")
        print("Или просто закройте окно, чтобы пропустить добавление фотографий")
        try:
            input("После копирования нажмите Enter...")
        except KeyboardInterrupt:
            shutil.rmtree(temp_dir)
            return ["", "", ""]  # Возвращаем пустые пути если окно закрыто

        if not os.path.exists(temp_dir):  # Если папка была закрыта
            return ["", "", ""]

        photos = [f for f in os.listdir(temp_dir) 
                 if os.path.splitext(f)[1].lower() in ('.jpg','.jpeg','.png','.gif')]
        
        if len(photos) > 3:
            shutil.rmtree(temp_dir)
            print("\nВыбрано больше 3 фотографий. Попробуйте снова.")
            if input("Нажмите Enter для повтора или 'q' для отмены: ").lower() == 'q':
                return ["", "", ""]
            continue
            
        valid_photos = []
        os.makedirs(photo_dir, exist_ok=True)
        
        for photo in photos:
            src_path = os.path.join(temp_dir, photo)
            if os.path.getsize(src_path) <= 2 * 1024 * 1024:  # 2MB
                dest_path = os.path.join(photo_dir, photo)
                shutil.copy2(src_path, dest_path)
                valid_photos.append(os.path.abspath(dest_path))
            else:
                print(f"\nФото {photo} больше 2MB и будет пропущено")
                
        shutil.rmtree(temp_dir)
        
        if not valid_photos:
            return ["", "", ""]
            
        return valid_photos + [""] * (3 - len(valid_photos))
		
def inject_recaptcha(driver):
    try:
        token = driver.execute_script("""
            return new Promise((resolve) => {
                grecaptcha.ready(function() {
                    grecaptcha.execute('6Ld2UMMUAAAAAHrjnIJST8wcfUdolcKR7rPH2Fmu', {action: 'submit'}).then(function(token) {
                        resolve(token);
                    });
                });
            });
        """)
        driver.execute_script(f"document.getElementById('GRR').value = '{token}';")
        print("[+] reCAPTCHA токен установлен")
    except Exception as e:
        print(f"[!] Ошибка reCAPTCHA: {e}")

#3. Блоки по логике работы
#3.1 Создание конфига
def select_region():
    """Выбор региона"""
    while True:
        clear_console()
        print("Выберите регион:")
        print("=" * 50)
        
        # Сортируем регионы по ID
        for region_id in sorted(REGIONS_WITH_POPULATION.keys()):
            region = REGIONS_WITH_POPULATION[region_id]
            print(f"{region_id} {region['name']} {region['population']}")
        
        print("=" * 50)
        region_id = input("Введите номер региона (или 'q' для выхода): ")
        
        if region_id.lower() == 'q':
            return None, None
            
        if region_id in REGIONS_WITH_POPULATION:
            return region_id, REGIONS_WITH_POPULATION[region_id]["name"]
            
        print("\nНеверный выбор. Попробуйте снова.")
        input("Нажмите Enter для продолжения...")

def select_place(region_id):
    """Выбор провинции"""
    while True:
        clear_console()
        print(f"Выберите провинцию для региона {REGIONS_WITH_POPULATION[region_id]['name']}:")
        print("=" * 50)
        
        places = REGIONS_WITH_POPULATION[region_id]['places']
        sorted_places = sorted(
            places.items(),
            key=lambda x: x[1]['population'],
            reverse=True
        )
        
        for place_id, place_data in sorted_places:
            print(f"{place_id} {place_data['name']} {place_data['population']}")
        
        print("=" * 50)
        place_id = input("Введите номер провинции (или 'q' для выхода): ")
        
        if place_id.lower() == 'q':
            return None, None
            
        if place_id in places:
            return place_id, places[place_id]["name"]
            
        print("\nНеверный выбор. Попробуйте снова.")
        input("Нажмите Enter для продолжения...")

def create_config():
    """Последовательное создание конфига"""
    # Получаем путь к директории скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    config = {}
    
    # 1. Выбор региона
    region_id, _ = select_region()
    if not region_id:
        return
    config["region_id"] = region_id
    
    # 2. Выбор провинции
    place_id, _ = select_place(region_id)
    if not place_id:
        return
    config["place"] = place_id
    
    # 3. Выбор возраста
    clear_console()
    print("Выберите возраст:")
    for age_id, age_desc in AGE_OPTIONS.items():
        print(f"{age_id}) {age_desc}")
    while True:
        age = input("\nВведите номер возраста (или 'q' для выхода): ")
        if age.lower() == 'q':
            return
        if age in AGE_OPTIONS:
            config["age"] = age
            break
        print("Неверный выбор. Попробуйте снова.")
    
    # 4. Выбор стиля
    clear_console()
    print("Выберите стиль:")
    for style_id, style_desc in STYLE_OPTIONS.items():
        print(f"{style_id}) {style_desc}")
    while True:
        style = input("\nВведите номер стиля (или 'q' для выхода): ")
        if style.lower() == 'q':
            return
        if style in STYLE_OPTIONS:
            config["style"] = style
            break
        print("Неверный выбор. Попробуйте снова.")
    
    # 5. Выбор типа тела
    clear_console()
    print("Выберите тип тела:")
    for body_id, body_desc in BODY_TYPE_OPTIONS.items():
        print(f"{body_id}) {body_desc}")
    while True:
        body = input("\nВведите номер типа тела (или 'q' для выхода): ")
        if body.lower() == 'q':
            return
        if body in BODY_TYPE_OPTIONS:
            config["body_type"] = body
            break
        print("Неверный выбор. Попробуйте снова.")
    
    # 6. Ввод имени
    clear_console()
    print("Сейчас откроется текстовый редактор для ввода имени...")
    name = create_temp_text_file("name.txt")
    if not name:
        print("Имя не может быть пустым")
        return
    config["name"] = name
    
    # 7. Ввод email
    clear_console()
    print("Сейчас откроется текстовый редактор для ввода email...")
    email = create_temp_text_file("email.txt")
    if not email:
        print("Email не может быть пустым")
        return
    config["email"] = email
    
    # 8. Создание файла сообщения
    clear_console()
    print("Сейчас откроется текстовый редактор для ввода сообщения...")
    message = create_temp_text_file("message.txt")
    if message:
        message_dir = os.path.join(script_dir, "message")
        os.makedirs(message_dir, exist_ok=True)
        message_filename = f"message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        message_path = os.path.join(message_dir, message_filename)
        with open(message_path, "w", encoding="utf-8") as f:
            f.write(message)
        config["message_file"] = os.path.abspath(message_path)
    else:
        print("Сообщение не может быть пустым")
        return
    
    # 9. Загрузка фотографий
    clear_console()
    print("Переходим к загрузке фотографий...")
    photos = handle_photo_upload()
    config["photos"] = photos
    
    # 10. Выбор режима отображения
    clear_console()
    while True:
        headless = input("Скрытый режим? (Y = не показывать работу, N = показывать): ").upper()
        if headless in ['Y', 'N']:
            config["headless"] = headless
            break
        print("Пожалуйста, введите Y или N")
    
    # Добавление остальных полей
    config["user_agent"] = ""
    config["password"] = ""
    config["token"] = ""
    
    # Сохранение конфига
    configs_dir = os.path.join(script_dir, "configs")
    os.makedirs(configs_dir, exist_ok=True)
    config_filename = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    config_path = os.path.join(configs_dir, config_filename)
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
    
    clear_console()
    print(f"Конфиг успешно сохранён: {config_path}")
    input("\nНажмите Enter для возврата в главное меню...")

#3.2 Удаление

def clean_config_and_delete_profile(config_path, config_name, base_dir):
    with open(config_path, 'r+', encoding='utf-8') as f:
        config = json.load(f)
        config["token"] = ""
        config["password"] = ""
        config["user_agent"] = ""
        f.seek(0)
        json.dump(config, f, indent=4, ensure_ascii=False)
        f.truncate()

    profile_dir = os.path.join(base_dir, 'cookies', config_name)
    if os.path.exists(profile_dir):
        shutil.rmtree(profile_dir)
        print(f"[+] Удалена папка профиля: {profile_dir}")

def delete_on_site(config_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_name = os.path.splitext(os.path.basename(config_path))[0]

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    profile_path = os.path.join(script_dir, 'cookies', config_name, 'profile')
    if not os.path.exists(profile_path):
        print(f"[!] Папка профиля не найдена: {profile_path}")
        return False

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--user-data-dir={profile_path}')
    chrome_options.add_argument('--lang=ja')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    if config.get("user_agent"):
        chrome_options.add_argument(f'--user-agent={config["user_agent"]}')
    if config.get("headless", "").upper() == "Y":
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        url = f'https://oshioki24.com/board/delete/{config["region_id"]}/{config["token"]}/'
        driver.get(url)

        for attempt in range(10):
            try:
                password_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "password"))
                )
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.NAME, "password")))
                time.sleep(1)
                password_input.clear()
                password_input.send_keys(config["password"])

                inject_recaptcha(driver)

                delete_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "form-submit"))
                )
                time.sleep(1)
                delete_button.click()

                WebDriverWait(driver, 10).until(
                    lambda d: any(x in d.page_source for x in ["削除しました", "パスワードが違います", "認証に失敗しました"])
                )

                page = driver.page_source
                if "削除しました" in page:
                    print(f"[+] Удаление прошло успешно.")
                    driver.quit()
                    return True
                elif "パスワードが違います" in page:
                    print(f"[x] Пароль неправильный.")
                    break
                elif "認証に失敗しました" in page:
                    print(f"[!] Ошибка аутентификации, попытка {attempt + 1}/10")
                    time.sleep(2)
                    continue
            except Exception as e:
                print(f"[!] Ошибка на попытке {attempt + 1}: {str(e)}")
                time.sleep(2)

    finally:
        if driver:
            driver.quit()
    return False

def delete_ad():
    clear_console()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    configs_dir = os.path.join(script_dir, 'configs')

    files = [f for f in os.listdir(configs_dir) if f.endswith('.json')]
    if not files:
        print("[!] Нет доступных конфигов")
        input("Нажмите Enter для возврата...")
        return

    region_display = []
    for f in files:
        try:
            with open(os.path.join(configs_dir, f), encoding='utf-8') as fp:
                data = json.load(fp)
                region_id = data.get("region_id", "?")
                region_display.append(f"{region_id}_{f}")
        except:
            region_display.append(f"?_ERROR_{f}")

    for i, name in enumerate(region_display):
        print(f"{i+1}) {name}")

    index = input("Выберите конфиг по номеру (или 'q' для выхода): ")
    if index.lower() == 'q':
        return

    if not index.isdigit() or not (1 <= int(index) <= len(files)):
        print("[!] Неверный выбор")
        return

    selected_file = files[int(index) - 1]
    full_path = os.path.join(configs_dir, selected_file)
    config_name = os.path.splitext(selected_file)[0]

    index = input("Выберите конфиг по номеру: ")
    if not index.isdigit() or not (1 <= int(index) <= len(files)):
        print("[!] Неверный выбор")
        return

    selected_file = files[int(index) - 1]
    full_path = os.path.join(configs_dir, selected_file)
    config_name = os.path.splitext(selected_file)[0]

    print("1) Очистить конфиг (удаление на сайте и очистка полей)")
    print("2) Удалить полностью (удаление на сайте и удаление файла + профиля)")
    mode = input("Выберите режим удаления: ")

    token_present = False
    with open(full_path, encoding='utf-8') as f:
        data = json.load(f)
        token_present = bool(data.get("token"))

    success = True
    if token_present:
        success = delete_on_site(full_path)

    if not success:
        print("[!] Удаление на сайте не удалось или не завершено")
        return

    if mode == "1":
        clean_config_and_delete_profile(full_path, config_name, script_dir)
        print("[✓] Конфиг очищен")
    elif mode == "2":
        # Удаление файлов message_file и photos
        with open(full_path, encoding='utf-8') as f:
            data = json.load(f)
            if data.get("message_file") and os.path.exists(data["message_file"]):
                os.remove(data["message_file"])
                print(f"[✓] Удалён файл сообщения: {data['message_file']}")
            if data.get("photos"):
                for photo in data["photos"]:
                    if photo and os.path.exists(photo):
                        os.remove(photo)
                        print(f"[✓] Удалено фото: {photo}")
        clean_config_and_delete_profile(full_path, config_name, script_dir)
        os.remove(full_path)
        print("[✓] Конфиг и профиль удалены")
    else:
        print("[!] Неверный режим удаления")

    input("Нажмите Enter для возврата в меню...")

#3.3 Публикация
def generate_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def get_desktop_user_agent():
    mobile_keywords = ['Mobile', 'Android', 'iPhone', 'iPad', 'Windows Phone', 'Opera Mini', 'IEMobile']
    browsers = [
        UserAgent().chrome,
        UserAgent().firefox,
        UserAgent().safari,
        UserAgent().edge,
        UserAgent().opera
    ]
    
    for _ in range(100):
        agent = random.choice(browsers)
        if not any(keyword in agent for keyword in mobile_keywords):
            return agent
    
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def setup_browser_options(config_path, user_agent=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_name = get_config_name(config_path)

    profile_path = os.path.join(script_dir, 'cookies', config_name, 'profile')
    os.makedirs(profile_path, exist_ok=True)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--user-data-dir={profile_path}')
    chrome_options.add_argument('--lang=ja')
    chrome_options.add_argument('--accept-language=ja-JP')
    chrome_options.add_experimental_option("prefs", {
        "profile.exit_type": "Normal",
        "profile.default_content_setting_values.notifications": 2,
        "profile.background_mode.enabled": False,
        "exit_type": "Normal"
    })

    if user_agent:
        chrome_options.add_argument(f'--user-agent={user_agent}')

    return chrome_options

def process_config(config_path):
    with open(config_path, 'r+', encoding='utf-8') as f:
        config = json.load(f)

        if not config.get('user_agent'):
            config['user_agent'] = get_desktop_user_agent()

        if not config.get('password'):
            config['password'] = generate_password()

        f.seek(0)
        json.dump(config, f, indent=4, ensure_ascii=False)
        f.truncate()

        chrome_options = setup_browser_options(config_path, config['user_agent'])

        if config.get('headless') == 'Y':
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')

        service = Service(os.path.join(os.path.dirname(__file__), 'chromedriver.exe'))
        service.log_path = os.devnull

        driver = None
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get(f'https://oshioki24.com/board/post/{config["region_id"]}/')

            # НОВОЕ: Получаем значение FB из скрытого поля
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, 'FB'))
            )
            fb_value = driver.find_element(By.NAME, 'FB').get_attribute('value')

            def fill_form():
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

                # Заполняем выпадающие списки
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

                # Заполняем сообщение
                with open(config['message_file'], 'r', encoding='utf-8') as msg_file:
                    message = msg_file.read()
                    message_element = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.NAME, 'message'))
                    )
                    message_element.clear()
                    message_element.send_keys(message)

                # Загружаем фото
                for i, photo_path in enumerate(config['photos'], 1):
                    if photo_path and photo_path.strip():
                        abs_photo_path = os.path.abspath(photo_path)
                        photo_input = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.NAME, f'photo{i}'))
                        )
                        photo_input.send_keys(abs_photo_path)
                        WebDriverWait(driver, 15).until(
                            lambda d: photo_input.get_attribute('value') != ''
                        )

                # НОВОЕ: Устанавливаем значение FB
                driver.execute_script(f"document.getElementById('FB').value = '{fb_value}';")

            def refill_credentials():
                # Обновляем FB при каждой попытке
                new_fb = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.NAME, 'FB'))
                ).get_attribute('value')
                driver.execute_script(f"document.getElementById('FB').value = '{new_fb}';")

                # Обновляем пароль
                password_field = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.NAME, 'password'))
                )
                password_field.clear()
                password_field.send_keys(config['password'])
                time.sleep(random.uniform(0.5, 1.5))

                # Перезагружаем фото
                for i, photo_path in enumerate(config['photos'], 1):
                    if photo_path and photo_path.strip():
                        abs_photo_path = os.path.abspath(photo_path)
                        photo_input = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.NAME, f'photo{i}'))
                        )
                        photo_input.send_keys(abs_photo_path)
                        WebDriverWait(driver, 15).until(
                            lambda d: photo_input.get_attribute('value') != ''
                        )

            fill_form()

            max_attempts = 5 if config.get('token') else 9
            attempt = 0

            while attempt < max_attempts:
                attempt += 1
                current_url = driver.current_url

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

                # Ожидаем изменения страницы
                try:
                    WebDriverWait(driver, 30).until(
                        EC.url_changes(current_url)
                    )
                except:
                    pass

                # Проверяем результат
                if '投稿ありがとうございました' in driver.page_source:
                    print("Успешная отправка!")
                    return True
                
                if '認証に失敗しました' in driver.page_source:
                    print(f"Попытка {attempt}/{max_attempts}: Ошибка аутентификации")
                    if attempt < max_attempts:
                        refill_credentials()
                        time.sleep(random.uniform(1, 3))
                    else:
                        return False

                # Проверка на блокировку
                if any(keyword in driver.page_source for keyword in ['アクセスが集中', '暫時利用出来ません']):
                    print("Обнаружена блокировка трафика")
                    return False

            return False

        except Exception as e:
            print(f"Критическая ошибка: {str(e)}")
            return False
        finally:
            if driver:
                driver.quit()

#3.4 Получение токена

def process_board_page(config_path):
    with open(config_path, 'r+', encoding='utf-8') as f:
        config = json.load(f)
        target_email = config['email']
        current_token = config['token']
        region_id = config['region_id']
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            try:
                headers = {'User-Agent': config['user_agent']}
                response = requests.get(f'https://oshioki24.com/board/{region_id}/', headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                panels = soup.find_all('div', class_='panel panel-default panel-board')
                for panel in panels:
                    email_link = panel.find('div', class_='panel-head').find('a')
                    if not email_link:
                        continue
                    href = email_link.get('href', '')
                    if '/cdn-cgi/l/email-protection#' in href:
                        protection_code = href.split('#')[-1] if '#' in href else href.split('/')[-1]
                        decrypted_email = decode_email(protection_code)
                        if decrypted_email == target_email:
                            report_button = panel.find('button', class_='modal-report-open')
                            if not report_button:
                                continue
                            new_token = report_button.get('id')
                            if new_token:
                                if current_token and new_token == current_token:
                                    time.sleep(15)
                                    break
                                config['token'] = new_token
                                f.seek(0)
                                json.dump(config, f, indent=4, ensure_ascii=False)
                                f.truncate()
                                return True
            except Exception:
                pass
            if attempt < max_attempts:
                time.sleep(15)
        return False

#3.5 обновление поста

def process_edit(config_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_name = os.path.splitext(os.path.basename(config_path))[0]
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    profile_path = os.path.join(script_dir, 'cookies', config_name, 'profile')
    if not os.path.exists(profile_path):
        print(f"[!] Папка профиля не найдена: {profile_path}")
        return
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--user-data-dir={profile_path}')
    chrome_options.add_argument('--lang=ja')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    if config.get("user_agent"):
        chrome_options.add_argument(f'--user-agent={config["user_agent"]}')
    if config.get("headless", "").upper() == "Y":
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        url = f'https://oshioki24.com/board/edit/{config["region_id"]}/{config["token"]}/'
        driver.get(url)
        for attempt in range(3):
            try:
                password_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "password"))
                )
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.NAME, "password")))
                time.sleep(1)
                password_input.clear()
                password_input.send_keys(config["password"])
                inject_recaptcha(driver)
                submit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "form-submit"))
                )
                time.sleep(1)
                submit_button.click()
                WebDriverWait(driver, 10).until(
                    lambda d: any(x in d.page_source for x in ["記事を修正いたしました", "認証に失敗しました"])
                )
                page = driver.page_source
                if "記事を修正いたしました" in page:
                    print("[+] Пост успешно обновлён.")
                    break
                elif "認証に失敗しました" in page:
                    print(f"[!] Ошибка аутентификации, попытка {attempt + 1}/3")
                    time.sleep(2)
                    continue
            except Exception as e:
                print(f"[!] Ошибка на попытке {attempt + 1}: {str(e)}")
                time.sleep(2)
    finally:
        if driver:
            driver.quit()

#3.5 Сканер/анализатор:

class ScannerManager:
    def __init__(self):
        self.scanners = {}
        self.state_file = "scanner_state.json"
        self.scanning_thread = None
        self.should_run = False
        self._lock = threading.Lock()
        self.load_state()

    def load_state(self):
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                self.is_forced_on = state.get('is_forced_on', False)
                self.is_forced_off = not self.is_forced_on
        except:
            self.is_forced_on = False
            self.is_forced_off = True

    def has_active_automatic_configs(self):
        try:
            configs = load_all_configs()
            return any(
                config.get('active') and config.get('mode') == '1'
                for config in configs.values()
            )
        except:
            return False

    def force_on(self):
        with self._lock:
            if not self.has_active_automatic_configs():
                self.is_forced_off = True
                self.is_forced_on = False
                self.save_state()
                return False
            
            self.is_forced_on = True
            self.is_forced_off = False
            self.save_state()
            self.start_scanning()
            return True

    def force_off(self):
        with self._lock:
            self.is_forced_off = True
            self.is_forced_on = False
            self.save_state()
            self.stop_scanning()

    def save_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump({'is_forced_on': self.is_forced_on}, f)
        except:
            pass

    def start_scanning(self):
        if self.scanning_thread and self.scanning_thread.is_alive():
            return
        
        self.should_run = True
        self.scanning_thread = threading.Thread(target=self._scanning_loop)
        self.scanning_thread.daemon = True
        self.scanning_thread.start()

    def stop_scanning(self):
        self.should_run = False
        if self.scanning_thread and self.scanning_thread.is_alive():
            self.scanning_thread.join(timeout=1.0)

    def _scanning_loop(self):
        while self.should_run and not self.is_forced_off:
            try:
                if not self.has_active_automatic_configs():
                    self.force_off()
                    break

                configs = load_all_configs()
                active_regions = set()
                
                for config in configs.values():
                    if config.get('active') and config.get('mode') == '1':
                        region_id = config.get('region_id')
                        if region_id:
                            active_regions.add(int(region_id))

                for region_id in active_regions:
                    if self.is_forced_off:
                        break
                        
                    scanner = self.get_scanner(region_id)
                    if scanner.should_scan():
                        try:
                            log_path = ensure_log_directory()
                            update_log_file(log_path, region_id, scanner)
                            scanner.update_last_scan_time()
                        except:
                            pass

                time.sleep(1)
            except:
                time.sleep(1)
                
    def get_scanner(self, region_id):
        with self._lock:
            if region_id not in self.scanners:
                self.scanners[region_id] = BoardScanner(region_id)
            return self.scanners[region_id]

scanner_manager = ScannerManager()

class BoardScanner:
    def __init__(self, board_number):
        self.board_number = board_number
        self.current_interval = MIN_SCAN_INTERVAL
        self.last_scan_time = datetime.now(JST)
        self.start_time = datetime.now(JST)
        
    def should_scan(self):
        current_time = datetime.now(JST)
        # Первые 35 минут сканируем каждую минуту
        if (current_time - self.start_time).total_seconds() < 2100:
            return True
        return current_time >= self.last_scan_time + timedelta(seconds=self.current_interval)
        
    def update_last_scan_time(self):
        self.last_scan_time = datetime.now(JST)

def get_profile_data(panel):
    try:
        email_link = panel.find('div', class_='panel-head').find('a')
        if not email_link:
            return None, None
            
        href = email_link.get('href', '')
        profile_title = email_link.text.strip()
        if not profile_title:
            return None, None
        
        if href.startswith('mailto:'):
            email = href.replace('mailto:', '')
        elif '/cdn-cgi/l/email-protection#' in href:
            protection_code = href.split('#')[-1] if '#' in href else href.split('/')[-1]
            email = decode_email(protection_code)
        else:
            return None, None
            
        return email, profile_title
    except:
        return None, None
		
def create_post_identifier(panel):
    email, profile_title = get_profile_data(panel)
    if email and profile_title:
        return f"{email}_{profile_title}"
    return None

def parse_jst_time(time_str):
    try:
        time_str = re.sub(r'\([月火水木金土日]\)', '', time_str.strip())
        dt = datetime.strptime(time_str, "%Y.%m.%d %H:%M")
        return JST.localize(dt)
    except Exception:
        return None

def get_board_posts(board_number, existing_data=None):
    base_url = f"{BASE_URL}{board_number}/"
    all_posts = []
    page = 1
    last_known_time = None
    
    if existing_data:
        all_timestamps = []
        for timestamps in existing_data.values():
            all_timestamps.extend(timestamps)
        if all_timestamps:
            last_known_time = max(all_timestamps)
    
    while page <= 9:
        url = f"{base_url}{page if page > 1 else ''}"
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                break
                
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            posts_found = False
            all_posts_new = True
            
            for panel in soup.find_all('div', class_='panel-board'):
                posts_found = True
                identifier = create_post_identifier(panel)
                if identifier:
                    time_elem = panel.find('div', class_='panel-time')
                    if time_elem:
                        time_text = time_elem.text.strip()
                        time_match = re.search(r'\d{4}\.\d{2}\.\d{2}(\(.\))? \d{2}:\d{2}', time_text)
                        if time_match:
                            timestamp = parse_jst_time(time_match.group())
                            if timestamp:
                                if last_known_time and timestamp <= last_known_time:
                                    all_posts_new = False
                                    break
                                all_posts.append((identifier, timestamp))
            
            if not posts_found or not all_posts_new:
                break
                
            page += 1
            
        except:
            break
    
    return all_posts

def update_log_file(log_path, board_number, board_scanner):
    log_file = os.path.join(log_path, f"log{board_number}.txt")
    current_time = datetime.now(JST)
    cutoff_time = current_time - timedelta(hours=3)
    
    existing_data = {}
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(', ')
                identifier = parts[0]
                timestamps = []
                for ts_str in parts[1:]:
                    try:
                        ts = parse_jst_time(ts_str)
                        if ts and ts > cutoff_time:
                            timestamps.append(ts)
                    except:
                        continue
                if timestamps:
                    existing_data[identifier] = timestamps

    all_posts = get_board_posts(board_number, existing_data)
    
    for identifier, timestamp in all_posts:
        if timestamp > cutoff_time:
            if identifier in existing_data:
                timestamps = existing_data[identifier]
                timestamps.append(timestamp)
                existing_data[identifier] = sorted(list(set(timestamps)))
            else:
                existing_data[identifier] = [timestamp]

    if (current_time - board_scanner.start_time).total_seconds() >= 2100:
        all_post_times = []
        for timestamps in existing_data.values():
            all_post_times.extend(timestamps)
        board_scanner.current_interval = calculate_optimal_interval(all_post_times)

    with open(log_file, 'w', encoding='utf-8') as f:
        for identifier, timestamps in existing_data.items():
            recent_timestamps = sorted([ts for ts in timestamps if ts > cutoff_time])
            if recent_timestamps:
                timestamp_strs = [ts.strftime("%Y.%m.%d(月) %H:%M") for ts in recent_timestamps]
                f.write(f"{identifier}, {', '.join(timestamp_strs)}\n")

def calculate_optimal_interval(post_timestamps):
    if not post_timestamps:
        return MIN_SCAN_INTERVAL
        
    sorted_times = sorted(post_timestamps)
    intervals = []
    
    for i in range(1, len(sorted_times)):
        interval = (sorted_times[i] - sorted_times[i-1]).total_seconds()
        if interval > 0:
            intervals.append(interval)
            
    if not intervals:
        return MIN_SCAN_INTERVAL
        
    median_interval = sorted(intervals)[len(intervals)//2]
    return max(MIN_SCAN_INTERVAL, min(MAX_SCAN_INTERVAL, int(median_interval * 0.8)))

def ensure_log_directory():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, LOG_DIR)
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    return log_path

#3.5 Меню + основной цикл

def show_statistics():
    clear_console()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, 'logs')
    now = datetime.now(pytz.timezone("Asia/Tokyo"))
    print("Статистика по регионам (последние 3 часа):")

    for region_id in sorted(REGIONS_WITH_POPULATION.keys()):
        log_file = os.path.join(log_dir, f"log{region_id}.txt")
        if not os.path.exists(log_file):
            continue

        post_times = []
        with open(log_file, encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(', ')
                timestamps = parts[1:]
                for ts in timestamps:
                    try:
                        dt = datetime.strptime(ts[:16], "%Y.%m.%d(%a) %H:%M").replace(tzinfo=pytz.timezone("Asia/Tokyo"))
                        if (now - dt).total_seconds() <= 10800:  # 3 часа
                            post_times.append(dt)
                    except:
                        continue

        if not post_times:
            continue

        intervals = [(post_times[i] - post_times[i-1]).total_seconds() for i in range(1, len(post_times))]
        avg_interval = sum(intervals)/len(intervals)/60 if intervals else 0

        print(f"Регион {region_id} ({REGIONS_WITH_POPULATION[region_id]['name']})")
        print(f" ├─ Объявлений: {len(post_times)}")
        print(f" └─ Средний интервал: {avg_interval:.1f} минут")

    input("Нажмите Enter для возврата в главное меню...")

def update_ad():
    clear_console()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    configs_dir = os.path.join(script_dir, 'configs')
    files = [f for f in os.listdir(configs_dir) if f.endswith('.json')]

    if not files:
        print("[!] Нет доступных конфигов")
        input("Нажмите Enter для возврата...")
        return

    region_display = []
    for f in files:
        try:
            with open(os.path.join(configs_dir, f), encoding='utf-8') as fp:
                data = json.load(fp)
                region_id = data.get("region_id", "?")
                region_display.append(f"{region_id}_{f}")
        except:
            region_display.append(f"?_ERROR_{f}")

    for i, name in enumerate(region_display):
        print(f"{i+1}) {name}")

    index = input("Выберите конфиг по номеру (или 'q' для выхода): ")
    if index.lower() == 'q':
        return

    if not index.isdigit() or not (1 <= int(index) <= len(files)):
        print("[!] Неверный выбор")
        return

    selected_file = files[int(index) - 1]
    full_path = os.path.join(configs_dir, selected_file)

    with open(full_path, 'r+', encoding='utf-8') as f:
        config = json.load(f)

        def update_field(field_name, description, current_value, options=None):
            if options:
                for k, v in options.items():
                    print(f"{k}) {v}")
            new_val = input(f"{description} [{current_value}]: ").strip()
            return new_val if new_val else current_value

        print("Регионы:")
        for rid, region in REGIONS_WITH_POPULATION.items():
            print(f"{rid}) {region['name']} ({region['population']})")
        config['region_id'] = update_field('region_id', 'Регион ID', config.get('region_id', ''))

        if config['region_id'] in REGIONS_WITH_POPULATION:
            print("Провинции:")
            places = REGIONS_WITH_POPULATION[config['region_id']]['places']
            for pid, pdata in places.items():
                print(f"{pid}) {pdata['name']} ({pdata['population']})")
        config['place'] = update_field('place', 'Провинция (place)', config.get('place', ''))

        print("Возраст:")
        config['age'] = update_field('age', 'Возраст (1-4)', config.get('age', ''), AGE_OPTIONS)
        print("Стиль:")
        config['style'] = update_field('style', 'Стиль (1-6)', config.get('style', ''), STYLE_OPTIONS)
        print("Тип тела:")
        config['body_type'] = update_field('body_type', 'Тип тела (1-8)', config.get('body_type', ''), BODY_TYPE_OPTIONS)

        print("Редактируем имя...")
        name = create_temp_text_file("name_edit.txt")
        if name:
            config['name'] = name

        print("Редактируем email...")
        email = create_temp_text_file("email_edit.txt")
        if email:
            config['email'] = email

        print("Редактируем сообщение...")
        message = create_temp_text_file("message_edit.txt")
        if message:
            with open(config['message_file'], "w", encoding="utf-8") as msgf:
                msgf.write(message)

        headless = input(f"Скрытый режим? (Y/N) [{config.get('headless', 'N')}]: ").upper()
        config['headless'] = headless if headless in ['Y', 'N'] else config.get('headless', 'N')

        f.seek(0)
        json.dump(config, f, indent=4, ensure_ascii=False)
        f.truncate()

    print("[✓] Конфиг обновлён.")
    input("Нажмите Enter для возврата в главное меню...")

def show_detailed_statistics():
    clear_console()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, 'logs')
    now = datetime.now(pytz.timezone("Asia/Tokyo"))
    print("Подробная статистика по авторам (последние 3 часа):")

    for region_id in sorted(REGIONS_WITH_POPULATION.keys()):
        log_file = os.path.join(log_dir, f"log{region_id}.txt")
        if not os.path.exists(log_file):
            continue

        with open(log_file, encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(', ')
                if len(parts) < 2:
                    continue

                author_id = parts[0]
                timestamps = []
                for ts in parts[1:]:
                    try:
                        dt = datetime.strptime(ts[:16], "%Y.%m.%d(%a) %H:%M").replace(tzinfo=pytz.timezone("Asia/Tokyo"))
                        if (now - dt).total_seconds() <= 10800:
                            timestamps.append(dt)
                    except:
                        continue

                if not timestamps:
                    continue

                timestamps.sort()
                last_time = timestamps[-1].strftime("%Y.%m.%d %H:%M")
                intervals = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]
                avg_interval = sum(intervals)/len(intervals)/60 if intervals else 0

                print(f"Автор: {author_id}")
                print(f" ├─ Публикаций: {len(timestamps)}")
                print(f" ├─ Последняя: {last_time}")
                print(f" └─ Средний интервал: {avg_interval:.1f} мин")

    input("Нажмите Enter для возврата в главное меню...")

def auto_posting_manager():
    STATE_FILE = "config_states.json"
    board_scanners = {}  # Хранилище сканеров для каждого конфига
    
    def run_configs():
        while running_configs:
            for filename, settings in list(running_configs.items()):
                config_path = os.path.join(configs_dir, filename)
                task_scheduler.add_task(config_path, 'post')
            time.sleep(60)
    
    def load_states():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                states = json.load(f)
                return {k: v for k, v in states.items() if v.get('active', False)}
        except:
            return {}
    
    def load_all_states():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_states(states):
        # Загружаем все существующие состояния
        all_states = load_all_states()
        # Обновляем состояния
        for fname, settings in states.items():
            settings['active'] = True
            all_states[fname] = settings
        # Для конфигов, которых нет в текущих состояниях, но есть в all_states,
        # устанавливаем active = False
        for fname in all_states:
            if fname not in states:
                all_states[fname]['active'] = False
        
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_states, f, indent=4, ensure_ascii=False)
    
    running_configs = load_states()

    def get_config_status(fname, settings):
        all_states = load_all_states()
        if fname not in running_configs:
            # Проверяем, есть ли сохраненные настройки
            if fname in all_states:
                return "отключен        "
            return "выключен         "
        
        mode = settings.get('mode')
        if mode == '1':
            return "включен  automatic"
        elif mode == '2':
            min_int = settings.get('min_interval', 0) // 60
            max_int = settings.get('max_interval', 0) // 60
            return f"включен  manual {min_int}-{max_int}min"
        return "включен           "

    def show_config_menu():
        clear_console()
        utc_now = datetime.utcnow()
        print(f"Current Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted): {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Current User's Login: {os.getlogin()}")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        configs_dir = os.path.join(script_dir, 'configs')
        files = [f for f in os.listdir(configs_dir) if f.endswith('.json')]

        if not files:
            print("[!] Нет доступных конфигов")
            input("Нажмите Enter для возврата...")
            return None

        print("\nДоступные конфиги:")
        for i, fname in enumerate(files):
            status = get_config_status(fname, running_configs.get(fname, {}))
            region = "unknown"
            try:
                with open(os.path.join(configs_dir, fname), 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    region = config.get("region_id", "unknown")
            except:
                pass
            print(f"{i+1}) {status} {region}_{fname}")

        print("\nВыберите действие:")
        print("a) Включить все")
        print("d) Выключить все")
        print("q) Выход в главное меню")
        print("\nИли введите номера конфигов через запятую (например: 1,3,4)")
        return files

    def get_intervals():
        while True:
            try:
                min_interval = int(input("Введите интервал в минутах от: "))
                max_interval = int(input("Введите интервал в минутах до: "))
                if min_interval > max_interval:
                    print("[!] Минимальный интервал не может быть больше максимального")
                    continue
                if min_interval < 1:
                    print("[!] Интервал не может быть меньше 1 минуты")
                    continue
                return min_interval, max_interval
            except ValueError:
                print("[!] Пожалуйста, введите числовое значение")

    def configure_config(filename):
        all_states = load_all_states()  # Изменено с load_states на load_all_states
        has_previous_settings = filename in all_states
    
        print(f"\nНастройка {filename}:")
        if has_previous_settings:
            print("1) Интелектуальный режим(сам подбирает лучше время)")
            print("2) Строгий режим(постить в интервалах от и до)")
            print("3) Включить с предыдущими настройками")
        else:
            print("1) Интелектуальный режим(сам подбирает лучше время)")
            print("2) Строгий режим(постить в интервалах от и до)")
        
        mode = input("→ ").strip()
    
        if mode == '3' and has_previous_settings:
            running_configs[filename] = all_states[filename]  # Используем all_states вместо saved_states
            running_configs[filename]['active'] = True
            print(f"[✓] Конфиг {filename} запущен с предыдущими настройками")
            return True
        elif mode == '1':
            running_configs[filename] = {'mode': '1', 'active': True}
            print(f"[✓] Конфиг {filename} запущен в автоматическом режиме")
            return True
        elif mode == '2':
            min_interval, max_interval = get_intervals()
            running_configs[filename] = {
                'mode': '2',
                'active': True,
                'min_interval': min_interval * 60,
                'max_interval': max_interval * 60
            }
            print(f"[✓] Конфиг {filename} запущен в ручном режиме")
            return True
        else:
            print("[!] Неверный выбор режима")
            return False

    def process_configs():
        while True:
            try:
                files = show_config_menu()
                if not files:
                    return False

                choice = input("→ ").strip().lower()
                
                if choice == 'q':
                    save_states(running_configs)
                    return False
                
                if choice == 'a':
                    # Загружаем все сохраненные состояния
                    all_states = load_all_states()
                    configs_changed = False
                    for fname in files:
                        if fname in all_states:
                            settings = all_states[fname].copy()  # Создаем копию настроек
                            settings['active'] = True
                            running_configs[fname] = settings
                            print(f"[✓] Конфиг {fname} включен с сохраненными настройками")
                            configs_changed = True
                    if configs_changed:
                        save_states(running_configs)
                    input("\nНажмите Enter для продолжения...")
                    continue
                
                if choice == 'd':
                    running_configs.clear()
                    save_states(running_configs)
                    continue

                indexes = [int(x.strip()) for x in choice.split(',') if x.strip().isdigit() and 0 < int(x) <= len(files)]
                if not indexes:
                    print("[!] Неверный ввод.")
                    continue

                selected_files = [files[i-1] for i in indexes]

                for filename in selected_files:
                    if filename in running_configs:
                        del running_configs[filename]
                        print(f"[✓] Конфиг {filename} остановлен")
                        save_states(running_configs)
                        continue

                    if configure_config(filename):
                        save_states(running_configs)

            except KeyboardInterrupt:
                save_states(running_configs)
                return False

    def get_optimal_posting_time(config_path, settings):
        """Определяет оптимальное время для следующего поста"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            region_id = config.get('region_id')
            if not region_id:
                return None

            # Получаем или создаем сканер для этого региона
            if region_id not in board_scanners:
                board_scanners[region_id] = BoardScanner(region_id)
            
            scanner = board_scanners[region_id]
            
            # Обновляем данные сканера если нужно
            if scanner.should_scan():
                log_path = ensure_log_directory()
                update_log_file(log_path, region_id, scanner)
                scanner.update_last_scan_time()
            
            # Получаем текущий оптимальный интервал
            current_time = datetime.now(JST)
            if settings.get('mode') == '1':  # Интеллектуальный режим
                # Используем интервал из сканера
                delay = scanner.current_interval
            else:  # Ручной режим
                delay = random.randint(
                    settings.get('min_interval', 300),
                    settings.get('max_interval', 360)
                )
            
            # Получаем время последнего поста
            last_time_str = config.get('last_posted')
            if last_time_str:
                last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
                last_time = JST.localize(last_time)
                next_time = last_time + timedelta(seconds=delay)
                if next_time > current_time:
                    return next_time
            
            return current_time + timedelta(seconds=delay)
            
        except Exception as e:
            print(f"Error calculating optimal time: {e}")
            return None

    def run_configs():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        configs_dir = os.path.join(script_dir, 'configs')

        while running_configs:
            for filename, settings in list(running_configs.items()):
                config_path = os.path.join(configs_dir, filename)
                try:
                    current_time = datetime.now(JST)
                    next_post_time = get_optimal_posting_time(config_path, settings)
                    
                    if not next_post_time or current_time < next_post_time:
                        continue

                    # Перенаправляем вывод браузера
                    original_stdout = sys.stdout
                    sys.stdout = open(os.devnull, 'w')
                    
                    success = process_config(config_path)
                    
                    # Восстанавливаем вывод
                    sys.stdout = original_stdout

                    if success:
                        with open(config_path, 'r+', encoding='utf-8') as f:
                            config = json.load(f)
                            config['last_posted'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
                            f.seek(0)
                            json.dump(config, f, ensure_ascii=False, indent=4)
                            f.truncate()
                        
                        token_success = process_board_page(config_path)
                        if not token_success:
                            print(f"[!] Не удалось обновить токен для {filename}")

                except Exception as e:
                    print(f"[!] Ошибка при обработке {filename}: {e}")

            time.sleep(60)

    # Основной цикл управления
    while True:
        try:
            if not process_configs():  # Если пользователь выбрал выход
                break
            if running_configs:  # Если есть активные конфиги
                try:
                    run_configs()  # Запускаем обработку конфигов
                except KeyboardInterrupt:
                    print("\n[!] Прервано пользователем")
                    continue  # Возвращаемся в меню конфигов
        except KeyboardInterrupt:
            save_states(running_configs)
            break  # Выход в главное меню

def update_ad():
    clear_console()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    configs_dir = os.path.join(script_dir, 'configs')
    files = [f for f in os.listdir(configs_dir) if f.endswith('.json')]

    if not files:
        print("[!] Нет доступных конфигов")
        input("Нажмите Enter для возврата...")
        return

    region_display = []
    for f in files:
        try:
            with open(os.path.join(configs_dir, f), encoding='utf-8') as fp:
                data = json.load(fp)
                region_id = data.get("region_id", "?")
                region_display.append(f"{region_id}_{f}")
        except:
            region_display.append(f"?_ERROR_{f}")

    for i, name in enumerate(region_display):
        print(f"{i+1}) {name}")

    index = input("Выберите конфиг по номеру (или 'q' для выхода): ")
    if index.lower() == 'q':
        return

    if not index.isdigit() or not (1 <= int(index) <= len(files)):
        print("[!] Неверный выбор")
        return

    selected_file = files[int(index) - 1]
    full_path = os.path.join(configs_dir, selected_file)

    with open(full_path, 'r+', encoding='utf-8') as f:
        config = json.load(f)

        def update_field(field_name, description, current_value, options=None):
            if options:
                for k, v in options.items():
                    print(f"{k}) {v}")
            new_val = input(f"{description} [{current_value}]: ").strip()
            return new_val if new_val else current_value

        print("Регионы:")
        for rid, region in REGIONS_WITH_POPULATION.items():
            print(f"{rid}) {region['name']} ({region['population']})")
        config['region_id'] = update_field('region_id', 'Регион ID', config.get('region_id', ''))
        if config['region_id'] in REGIONS_WITH_POPULATION:
            print("Провинции:")
            places = REGIONS_WITH_POPULATION[config['region_id']]['places']
            for pid, pdata in places.items():
                print(f"{pid}) {pdata['name']} ({pdata['population']})")
        config['place'] = update_field('place', 'Провинция (place)', config.get('place', ''))

        print("Возраст:")
        config['age'] = update_field('age', 'Возраст (1-4)', config.get('age', ''), AGE_OPTIONS)
        print("Стиль:")
        config['style'] = update_field('style', 'Стиль (1-6)', config.get('style', ''), STYLE_OPTIONS)
        print("Тип тела:")
        config['body_type'] = update_field('body_type', 'Тип тела (1-8)', config.get('body_type', ''), BODY_TYPE_OPTIONS)

        print("Редактируем имя...")
        name = create_temp_text_file("name_edit.txt")
        if name:
            config['name'] = name

        print("Редактируем email...")
        email = create_temp_text_file("email_edit.txt")
        if email:
            config['email'] = email

        print("Редактируем сообщение...")
        message = create_temp_text_file("message_edit.txt")
        if message:
            with open(config['message_file'], "w", encoding="utf-8") as msgf:
                msgf.write(message)

        headless = input(f"Скрытый режим? (Y/N) [{config.get('headless', 'N')}]: ").upper()
        config['headless'] = headless if headless in ['Y', 'N'] else config.get('headless', 'N')

        f.seek(0)
        json.dump(config, f, indent=4, ensure_ascii=False)
        f.truncate()

    print("[✓] Конфиг обновлён.")
    input("Нажмите Enter для возврата в главное меню...")

class TaskScheduler:
    def __init__(self):
        self.tasks_queue = []
        self.current_task = None
        self._lock = threading.Lock()
        self.running = False
        self.scheduler_thread = None

    def add_task(self, config_path, task_type, priority=0):
        with self._lock:
            task = {
                'config_path': config_path,
                'type': task_type,  # 'post', 'repost', 'delete', etc.
                'priority': priority,
                'scheduled_time': None,
                'state': 'pending'
            }
            
            if task_type == 'post':
                # Используем интеллектуальный режим для определения времени
                next_time = self._calculate_next_post_time(config_path)
                task['scheduled_time'] = next_time
            
            self.tasks_queue.append(task)
            self.tasks_queue.sort(key=lambda x: (x['scheduled_time'] or datetime.max, -x['priority']))

    def _calculate_next_post_time(self, config_path):
        # Интеллектуальный режим определения времени
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            region_id = config.get('region_id')
            scanner = scanner_manager.get_scanner(region_id)
            
            current_time = datetime.now(JST)
            optimal_interval = calculate_optimal_interval(scanner.get_post_times())
            
            last_post_time = config.get('last_posted')
            if last_post_time:
                last_time = datetime.strptime(last_post_time, "%Y-%m-%d %H:%M:%S")
                last_time = JST.localize(last_time)
                return last_time + timedelta(seconds=optimal_interval)
            
            return current_time + timedelta(seconds=optimal_interval)
        except:
            return datetime.now(JST) + timedelta(minutes=15)

    def start(self):
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            return

        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()

    def stop(self):
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=1.0)

    def _scheduler_loop(self):
        while self.running:
            try:
                with self._lock:
                    now = datetime.now(JST)
                    if self.tasks_queue and not self.current_task:
                        next_task = self.tasks_queue[0]
                        if next_task['scheduled_time'] <= now:
                            self.current_task = self.tasks_queue.pop(0)
                            self._execute_task(self.current_task)
                            self.current_task = None
            except:
                pass
            time.sleep(1)

    def _execute_task(self, task):
        try:
            if task['type'] == 'post':
                process_config(task['config_path'])
            elif task['type'] == 'repost':
                process_edit(task['config_path'])
            elif task['type'] == 'delete':
                delete_on_site(task['config_path'])
        except:
            pass

task_scheduler = TaskScheduler()

def main():
    """Основной цикл программы"""
    # Не запускаем сканер автоматически при старте
    while True:
        clear_console()
        print("\n================= Главное Меню =================")
        print("1) Создать конфиг")
        print("2) Статистика")
        print("3) Подробная статистика")
        print("4) Удалить объявление")
        print("5) Обновить объявление")
        print("6) Автопостинг / Автоперепубликация")
        print(f"7) {'Выключить' if scanner_manager.is_forced_on else 'Включить'} сканер")
        print("e) Выход")
        print("=" * 47)
        
        choice = input("\nВыберите пункт меню: ").lower()
        
        if choice == "1":
            create_config()
        elif choice == "2":
            show_statistics()
        elif choice == "3":
            show_detailed_statistics()
        elif choice == "4":
            delete_ad()
        elif choice == "5":
            update_ad()
        elif choice == "6":
            auto_posting_manager()
        elif choice == "7":
            if scanner_manager.is_forced_off:
                if not scanner_manager.force_on():  # Не включаем если нет активных автоматических конфигов
                    continue
            else:
                scanner_manager.force_off()
            continue

            # Сразу очищаем экран и показываем меню без дополнительных сообщений
        elif choice == "e":
            scanner_manager.stop_scanning()
            clear_console()
            print("Выход из программы...")
            break
        else:
            print("\nНеверный выбор. Попробуйте снова.")
            input("Нажмите Enter для продолжения...")

def load_all_configs():
    configs = {}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    configs_dir = os.path.join(script_dir, 'configs')
    
    for filename in os.listdir(configs_dir):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(configs_dir, filename), 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Явно устанавливаем active только если режим автоматический
                    if config.get('mode') == '1':
                        config['active'] = True
                    else:
                        config['active'] = False
                    configs[filename] = config
            except:
                continue
    return configs

if __name__ == "__main__":
    scanner_manager = ScannerManager()
    # Проверяем сохраненное состояние
    if not scanner_manager.is_forced_off:  # Если сканер не был выключен
        scanner_manager.start_scanning()
    main()