import requests
from bs4 import BeautifulSoup
import time

from CEACStatusBot.captcha import CaptchaHandle, OnnxCaptchaHandle


def query_status(application_num, passport_number, surname, captchaHandle: CaptchaHandle = OnnxCaptchaHandle("captcha.onnx")):
    failCount = 0
    result = {"success": False}

    while failCount < 5:
        if failCount > 0:
            time.sleep(5)
        failCount += 1

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        session = requests.Session()
        ROOT = "https://ceac.state.gov"

        try:
            r = session.get(f"{ROOT}/ceacstattracker/status.aspx?App=IV", headers=headers)
        except Exception:
            continue

        soup = BeautifulSoup(r.text, "lxml")

        captcha_img = soup.find("img", id="c_status_ctl00_contentplaceholder1_defaultcaptcha_CaptchaImage")
        if not captcha_img:
            continue

        img_url = ROOT + captcha_img["src"]
        img_resp = session.get(img_url)
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
            r = session.post(f"{ROOT}/ceacstattracker/status.aspx", headers=headers, data=data)
        except Exception:
            continue

        # <-- WAIT 5 SECONDS BEFORE PARSING RESULTS
        time.sleep(5)

        soup = BeautifulSoup(r.text, "lxml")

        status_el = soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblStatus")
        case_el = soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblCaseNo")

        if not status_el or not case_el:
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
