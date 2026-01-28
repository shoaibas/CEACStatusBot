import requests
from bs4 import BeautifulSoup
import time
from CEACStatusBot.captcha import CaptchaHandle, OnnxCaptchaHandle

def query_status(application_num, passport_number, surname, captchaHandle: CaptchaHandle = OnnxCaptchaHandle("captcha.onnx")):
    failCount = 0
    result = {"success": False}
    ROOT = "https://ceac.state.gov"

    while failCount < 5:
        if failCount > 0:
            # exponential backoff for retries
            time.sleep(10 * failCount)
        failCount += 1

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        session = requests.Session()
        try:
            r = session.get(f"{ROOT}/ceacstattracker/status.aspx?App=IV", headers=headers, timeout=15)
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
            print("GET failed, retrying...")
            continue

        soup = BeautifulSoup(r.text, "lxml")

        captcha_img = soup.find("img", id="c_status_ctl00_contentplaceholder1_defaultcaptcha_CaptchaImage")
        if not captcha_img:
            print("Captcha image not found, retrying...")
            continue

        img_url = ROOT + captcha_img["src"]
        try:
            img_resp = session.get(img_url, timeout=15)
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
            print("Captcha image GET failed, retrying...")
            continue

        captcha_value = captchaHandle.solve(img_resp.content)

        def copy_hidden(name, data):
            el = soup.find("input", {"name": name})
            if el:
                data[name] = el.get("value", "")

        data = {
            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnSubmit",
            "__EVENTARGUMENT": "",
            "__ASYNCPOST": "true",
            "ctl00$ContentPlaceHolder1$Visa_Case_Number": application_num,
            "ctl00$ContentPlaceHolder1$Passport_Number": passport_number,
            "ctl00$ContentPlaceHolder1$Surname": surname,
            "ctl00$ContentPlaceHolder1$Captcha": captcha_value,
        }

        for field in [
            "__VIEWSTATE",
            "__VIEWSTATEGENERATOR",
            "LBD_VCID_c_status_ctl00_contentplaceholder1_defaultcaptcha",
            "LBD_BackWorkaround_c_status_ctl00_contentplaceholder1_defaultcaptcha",
        ]:
            copy_hidden(field, data)

        try:
            r = session.post(f"{ROOT}/ceacstattracker/status.aspx", headers=headers, data=data, timeout=15)
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
            print("POST failed, retrying...")
            continue

        # wait 5 seconds after submitting before parsing results
        time.sleep(5)
        soup = BeautifulSoup(r.text, "lxml")

        status_el = soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblStatus")
        case_el = soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblCaseNo")

        if not status_el or not case_el:
            print("Status or case number not found, retrying...")
            continue

        msg_el = soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblMessage")
        visa_el = soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblAppName")

        result.update({
            "success": True,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "visa_type": visa_el.text.strip() if visa_el else "IV",
            "status": status_el.text.strip(),
            "description": msg_el.text.strip() if msg_el else "",
            "application_num": case_el.text.strip(),
            "application_num_origin": application_num,
            "case_created": None,
            "case_last_updated": None,
        })

        break

    return result
